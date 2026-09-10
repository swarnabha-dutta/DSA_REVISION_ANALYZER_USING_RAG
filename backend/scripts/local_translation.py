"""
Local Hindi -> English translation using IndicTrans2 ONNX.

This module provides a reusable local translation engine for the
DSA Revision Analyzer.

Why this exists:
    - Avoid unnecessary Groq API usage.
    - Avoid Groq translation quota for normal transcript translation.
    - Run translation locally on CPU using ONNX Runtime.
    - Keep the translation engine independent from the transcript
      checkpoint / resume logic.

Current model:
    hari31416/indictrans2-indic-en-dist-200M-ONNX-int8

The model is downloaded automatically through Hugging Face and then
cached locally.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer

from indicnlp.normalize.indic_normalize import IndicNormalizerFactory
from indicnlp.tokenize import indic_tokenize
from sacremoses import MosesDetokenizer


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_ID = "hari31416/indictrans2-indic-en-dist-200M-ONNX-int8"

DEFAULT_MAX_NEW_TOKENS = 128

SRC_LANG = "hin_Deva"
TGT_LANG = "eng_Latn"


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _past_feed(
    past_outputs: list[np.ndarray],
    num_layers: int,
) -> dict[str, np.ndarray]:
    """
    Build the decoder-with-past input dictionary.

    IndicTrans2 exports four cached tensors per transformer layer:

        decoder.key
        decoder.value
        encoder.key
        encoder.value
    """

    feed: dict[str, np.ndarray] = {}

    for layer_index in range(num_layers):
        base = layer_index * 4

        feed[
            f"past_key_values.{layer_index}.decoder.key"
        ] = past_outputs[base]

        feed[
            f"past_key_values.{layer_index}.decoder.value"
        ] = past_outputs[base + 1]

        feed[
            f"past_key_values.{layer_index}.encoder.key"
        ] = past_outputs[base + 2]

        feed[
            f"past_key_values.{layer_index}.encoder.value"
        ] = past_outputs[base + 3]

    return feed


# ============================================================
# LOCAL TRANSLATOR
# ============================================================


class LocalIndicTransTranslator:
    """
    Reusable IndicTrans2 ONNX translator.

    The model is loaded once when this class is initialized.

    Example:

        translator = LocalIndicTransTranslator()

        english = translator.translate(
            "ठीक है भाई साहब आज टू पॉइंटर पैटर्न है।"
        )

        print(english)
    """

    def __init__(
        self,
        model_id: str = MODEL_ID,
        providers: Optional[list[str]] = None,
    ) -> None:

        self.model_id = model_id

        # ----------------------------------------------------
        # Resolve / download model
        # ----------------------------------------------------

        self.model_path = Path(
            snapshot_download(model_id)
        )

        # ----------------------------------------------------
        # Runtime provider
        # ----------------------------------------------------

        self.providers = providers or [
            "CPUExecutionProvider"
        ]

        # ----------------------------------------------------
        # Hindi normalizer
        # ----------------------------------------------------

        normalizer_factory = (
            IndicNormalizerFactory()
        )

        self.normalizer = (
            normalizer_factory.get_normalizer("hi")
        )

        # ----------------------------------------------------
        # Target English detokenizer
        # ----------------------------------------------------

        self.detokenizer = MosesDetokenizer(
            lang="en"
        )

        # ----------------------------------------------------
        # Tokenizers
        # ----------------------------------------------------

        self.src_tokenizer = Tokenizer.from_file(
            str(
                self.model_path
                / "tokenizer_src.json"
            )
        )

        self.tgt_tokenizer = Tokenizer.from_file(
            str(
                self.model_path
                / "tokenizer_tgt.json"
            )
        )

        # ----------------------------------------------------
        # Tokenizer metadata
        # ----------------------------------------------------

        metadata_path = (
            self.model_path
            / "tokenizer_meta.json"
        )

        self.metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        # ----------------------------------------------------
        # Generation configuration
        # ----------------------------------------------------

        generation_config_path = (
            self.model_path
            / "generation_config.json"
        )

        generation_config: dict = {}

        if generation_config_path.exists():

            generation_config = json.loads(
                generation_config_path.read_text(
                    encoding="utf-8"
                )
            )

        self.decoder_start_id = int(
            generation_config.get(
                "decoder_start_token_id",
                2,
            )
        )

        self.eos_id = int(
            generation_config.get(
                "eos_token_id",
                2,
            )
        )

        # ----------------------------------------------------
        # ONNX sessions
        # ----------------------------------------------------

        self.encoder = ort.InferenceSession(
            str(
                self.model_path
                / "encoder_model.onnx"
            ),
            providers=self.providers,
        )

        self.decoder = ort.InferenceSession(
            str(
                self.model_path
                / "decoder_model.onnx"
            ),
            providers=self.providers,
        )

        self.decoder_with_past = (
            ort.InferenceSession(
                str(
                    self.model_path
                    / "decoder_with_past_model.onnx"
                ),
                providers=self.providers,
            )
        )

        # ----------------------------------------------------
        # Infer number of transformer layers
        #
        # Decoder outputs:
        #
        #     1 logits tensor
        #     +
        #     4 cached tensors per layer
        # ----------------------------------------------------

        self.num_layers = (
            len(
                self.decoder.get_outputs()
            )
            - 1
        ) // 4

    # ========================================================
    # PREPROCESSING
    # ========================================================

    def _preprocess_hindi(
        self,
        text: str,
    ) -> str:
        """
        Normalize and tokenize Hindi text.

        IndicTrans2 expects language tags followed by the
        normalized Hindi text.
        """

        normalized = self.normalizer.normalize(
            text
        )

        tokens = indic_tokenize.trivial_tokenize(
            normalized,
            lang="hi",
        )

        return (
            f"{SRC_LANG} "
            f"{TGT_LANG} "
            f"{' '.join(tokens)}"
        )

    # ========================================================
    # TRANSLATION
    # ========================================================

    def translate(
        self,
        text: str,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    ) -> str:
        """
        Translate Hindi/Hinglish text to English.

        Args:
            text:
                Hindi/Hinglish input text.

            max_new_tokens:
                Maximum number of tokens generated by the
                decoder.

        Returns:
            English translation.
        """

        if not isinstance(
            text,
            str,
        ):
            raise TypeError(
                "text must be a string."
            )

        text = text.strip()

        if not text:
            return ""

        # ----------------------------------------------------
        # 1. Preprocess
        # ----------------------------------------------------

        processed = (
            self._preprocess_hindi(text)
        )

        # ----------------------------------------------------
        # 2. Tokenize
        # ----------------------------------------------------

        encoded = (
            self.src_tokenizer.encode(
                processed
            )
        )

        input_ids = np.array(
            [
                [
                    token_id
                    if token_id
                    < self.metadata[
                        "src_dict_size"
                    ]
                    else self.metadata[
                        "unk_id"
                    ]
                    for token_id
                    in encoded.ids
                ]
            ],
            dtype=np.int64,
        )

        attention_mask = np.array(
            [
                encoded.attention_mask
            ],
            dtype=np.int64,
        )

        # ----------------------------------------------------
        # 3. Encoder
        # ----------------------------------------------------

        encoder_output = (
            self.encoder.run(
                ["last_hidden_state"],
                {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                },
            )[0]
        )

        # ----------------------------------------------------
        # 4. Decoder initialization
        # ----------------------------------------------------

        decoder_input_ids = np.array(
            [
                [
                    self.decoder_start_id
                ]
            ],
            dtype=np.int64,
        )

        output_ids = [
            self.decoder_start_id
        ]

        past_outputs: (
            list[np.ndarray] | None
        ) = None

        # ----------------------------------------------------
        # 5. Greedy decoding
        # ----------------------------------------------------

        for step in range(
            max_new_tokens
        ):

            if step == 0:

                decoder_outputs = (
                    self.decoder.run(
                        None,
                        {
                            "input_ids":
                                decoder_input_ids,

                            "encoder_hidden_states":
                                encoder_output,

                            "encoder_attention_mask":
                                attention_mask,
                        },
                    )
                )

            else:

                if past_outputs is None:
                    raise RuntimeError(
                        "Decoder cache was not initialized."
                    )

                decoder_outputs = (
                    self.decoder_with_past.run(
                        None,
                        {
                            "input_ids":
                                decoder_input_ids,

                            "encoder_attention_mask":
                                attention_mask,

                            **_past_feed(
                                past_outputs,
                                self.num_layers,
                            ),
                        },
                    )
                )

            # First output = logits
            logits = decoder_outputs[0]

            # Remaining outputs = KV cache
            past_outputs = list(
                decoder_outputs[1:]
            )

            next_token_id = int(
                np.argmax(
                    logits[
                        0,
                        -1,
                        :
                    ]
                )
            )

            # Stop at EOS
            if (
                next_token_id
                == self.eos_id
            ):
                break

            output_ids.append(
                next_token_id
            )

            decoder_input_ids = np.array(
                [
                    [
                        next_token_id
                    ]
                ],
                dtype=np.int64,
            )

        # ----------------------------------------------------
        # 6. Decode target tokens
        # ----------------------------------------------------

        safe_ids = [
            token_id
            if token_id
            < self.metadata[
                "tgt_dict_size"
            ]
            else self.metadata[
                "unk_id"
            ]
            for token_id
            in output_ids
        ]

        raw_output = (
            self.tgt_tokenizer.decode(
                safe_ids,
                skip_special_tokens=True,
            )
        )

        # ----------------------------------------------------
        # 7. English detokenization
        # ----------------------------------------------------

        english = (
            self.detokenizer.detokenize(
                raw_output.split()
            )
        )

        return english.strip()


# ============================================================
# SINGLETON
# ============================================================

_translator: (
    LocalIndicTransTranslator | None
) = None


def get_local_translator() -> LocalIndicTransTranslator:
    """
    Return a cached translator instance.

    The ONNX models are expensive to load, so the same instance
    should be reused instead of loading the model for every
    transcript segment.
    """

    global _translator

    if _translator is None:

        _translator = (
            LocalIndicTransTranslator()
        )

    return _translator


# ============================================================
# SIMPLE PUBLIC FUNCTION
# ============================================================


def translate_local(
    text: str,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
) -> str:
    """
    Convenience function for local Hindi -> English translation.

    Example:

        english = translate_local(
            "आज टू पॉइंटर पैटर्न है।"
        )
    """

    translator = (
        get_local_translator()
    )

    return translator.translate(
        text,
        max_new_tokens=max_new_tokens,
    )