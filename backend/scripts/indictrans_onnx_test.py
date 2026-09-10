from pathlib import Path
import json

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer

from indicnlp.normalize.indic_normalize import IndicNormalizerFactory
from indicnlp.tokenize import indic_tokenize
from sacremoses import MosesDetokenizer


# ============================================================
# Configuration
# ============================================================

MODEL_ID = "hari31416/indictrans2-indic-en-dist-200M-ONNX-int8"


# ============================================================
# Download / locate model
# ============================================================

model_path = Path(
    snapshot_download(MODEL_ID)
)

print("=" * 60)
print("IndicTrans2 ONNX Translation Test")
print("=" * 60)
print(f"Model path: {model_path}")


# ============================================================
# Hindi preprocessing
# ============================================================

normalizer = IndicNormalizerFactory().get_normalizer("hi")
detokenizer = MosesDetokenizer(lang="en")


def preprocess_hindi(text: str) -> str:
    """
    Normalize and tokenize Hindi text, then add
    IndicTrans2 source/target language tags.
    """

    text = normalizer.normalize(text.strip())

    tokens = indic_tokenize.trivial_tokenize(
        text,
        "hi",
    )

    processed = " ".join(tokens)

    return f"hin_Deva eng_Latn {processed}"


# ============================================================
# Load tokenizers
# ============================================================

print("\nLoading tokenizers...")

src_tok = Tokenizer.from_file(
    str(model_path / "tokenizer_src.json")
)

tgt_tok = Tokenizer.from_file(
    str(model_path / "tokenizer_tgt.json")
)

print("Tokenizers loaded successfully")


# ============================================================
# Load ONNX models
# ============================================================

print("\nLoading ONNX models...")

enc = ort.InferenceSession(
    str(model_path / "encoder_model.onnx"),
    providers=["CPUExecutionProvider"],
)

dec = ort.InferenceSession(
    str(model_path / "decoder_model.onnx"),
    providers=["CPUExecutionProvider"],
)

dec_past = ort.InferenceSession(
    str(model_path / "decoder_with_past_model.onnx"),
    providers=["CPUExecutionProvider"],
)

print("ONNX models loaded successfully")


# ============================================================
# Generation configuration
# ============================================================

gen_cfg = json.loads(
    (model_path / "generation_config.json").read_text(
        encoding="utf-8"
    )
)

decoder_start_id = int(
    gen_cfg.get(
        "decoder_start_token_id",
        2,
    )
)

eos_id = int(
    gen_cfg.get(
        "eos_token_id",
        2,
    )
)


# ============================================================
# Tokenizer metadata
# ============================================================

meta = json.loads(
    (model_path / "tokenizer_meta.json").read_text(
        encoding="utf-8"
    )
)


# Number of Transformer layers
num_layers = (
    len(dec.get_outputs()) - 1
) // 4


# ============================================================
# Past-key-value helper
# ============================================================

def past_feed(past_outputs):
    """
    Convert decoder past outputs into the input dictionary
    expected by decoder_with_past_model.onnx.
    """

    feed = {}

    for i in range(num_layers):

        base = i * 4

        feed[
            f"past_key_values.{i}.decoder.key"
        ] = past_outputs[base]

        feed[
            f"past_key_values.{i}.decoder.value"
        ] = past_outputs[base + 1]

        feed[
            f"past_key_values.{i}.encoder.key"
        ] = past_outputs[base + 2]

        feed[
            f"past_key_values.{i}.encoder.value"
        ] = past_outputs[base + 3]

    return feed


# ============================================================
# Translation
# ============================================================

def translate(
    text: str,
    max_new_tokens: int = 128,
) -> str:

    # --------------------------------------------------------
    # 1. Preprocess Hindi
    # --------------------------------------------------------

    processed = preprocess_hindi(text)

    print("\nPreprocessed input:")
    print(processed)

    # --------------------------------------------------------
    # 2. Tokenize
    # --------------------------------------------------------

    encoded = src_tok.encode(processed)

    input_ids = np.array(
        [
            [
                token_id
                if token_id < meta["src_dict_size"]
                else meta["unk_id"]
                for token_id in encoded.ids
            ]
        ],
        dtype=np.int64,
    )

    attention_mask = np.array(
        [encoded.attention_mask],
        dtype=np.int64,
    )

    # --------------------------------------------------------
    # 3. Encoder
    # --------------------------------------------------------

    enc_out = enc.run(
        ["last_hidden_state"],
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        },
    )[0]

    # --------------------------------------------------------
    # 4. Decoder initialization
    # --------------------------------------------------------

    decoder_input_ids = np.array(
        [[decoder_start_id]],
        dtype=np.int64,
    )

    output_ids = [decoder_start_id]

    past_outputs = None

    # --------------------------------------------------------
    # 5. Greedy decoding
    # --------------------------------------------------------

    for step in range(max_new_tokens):

        if step == 0:

            outputs = dec.run(
                None,
                {
                    "input_ids": decoder_input_ids,
                    "encoder_hidden_states": enc_out,
                    "encoder_attention_mask": attention_mask,
                },
            )

        else:

            outputs = dec_past.run(
                None,
                {
                    "input_ids": decoder_input_ids,
                    "encoder_attention_mask": attention_mask,
                    **past_feed(past_outputs),
                },
            )

        # First output = logits
        logits = outputs[0]

        # Remaining outputs = cached key/value tensors
        past_outputs = list(outputs[1:])

        # Greedy decoding
        next_id = int(
            np.argmax(
                logits[0, -1, :]
            )
        )

        # Stop when EOS is generated
        if next_id == eos_id:
            break

        output_ids.append(next_id)

        decoder_input_ids = np.array(
            [[next_id]],
            dtype=np.int64,
        )

    # --------------------------------------------------------
    # 6. Decode target tokens
    # --------------------------------------------------------

    safe_ids = [
        token_id
        if token_id < meta["tgt_dict_size"]
        else meta["unk_id"]
        for token_id in output_ids
    ]

    raw_output = tgt_tok.decode(
        safe_ids,
        skip_special_tokens=True,
    )

    # --------------------------------------------------------
    # 7. English detokenization
    # --------------------------------------------------------

    result = detokenizer.detokenize(
        raw_output.split()
    )

    return result


# ============================================================
# Main test
# ============================================================

if __name__ == "__main__":

    text = (
        "ठीक है भाई साहब लेक्चर थ्री है "
        "आज टू पॉइंटर पैटर्न का।"
    )

    print("\nInput:")
    print(text)

    result = translate(text)

    print("\nTranslation:")
    print(result)

    print("\n" + "=" * 60)
    print("Translation test completed")
    print("=" * 60)