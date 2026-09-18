function formatTimestamp(seconds) {
    const value =
        Number(seconds);

    if (
        !Number.isFinite(value) ||
        value < 0
    ) {
        return null;
    }

    const totalSeconds =
        Math.floor(value);

    const hours =
        Math.floor(
            totalSeconds / 3600
        );

    const minutes =
        Math.floor(
            (totalSeconds % 3600) / 60
        );

    const remainingSeconds =
        totalSeconds % 60;


    if (hours > 0) {

        return (
            `${String(hours).padStart(2, "0")}:` +
            `${String(minutes).padStart(2, "0")}:` +
            `${String(remainingSeconds).padStart(2, "0")}`
        );
    }


    return (
        `${String(minutes).padStart(2, "0")}:` +
        `${String(remainingSeconds).padStart(2, "0")}`
    );
}


function formatScore(result) {

    const rerankerScore =
        Number(
            result?.reranker_score
        );

    if (
        Number.isFinite(
            rerankerScore
        )
    ) {
        return rerankerScore.toFixed(
            3
        );
    }


    const rrfScore =
        Number(
            result?.rrf_score
        );

    if (
        Number.isFinite(
            rrfScore
        )
    ) {
        return rrfScore.toFixed(
            3
        );
    }


    return null;
}


function extractEpisodeNumber(title) {

    if (!title) {
        return null;
    }

    const match =
        String(title).match(
            /episode\s*[-:]?\s*(\d+)/i
        );

    if (!match) {
        return null;
    }

    return Number(
        match[1]
    );
}


export default function SearchResult({
    result,
    onOpen,
}) {

    if (!result) {
        return null;
    }


    const timestamp =
        formatTimestamp(
            result.timestamp_start
        );


    const score =
        formatScore(
            result
        );


    const patternName =
        result.pattern ||
        "DSA VIDEO";


    /*
     * IMPORTANT:
     *
     * video_id is intentionally NOT used
     * as a UI fallback anymore.
     *
     * Raw IDs should stay internal.
     */

    const videoTitle =
        result.video_title ||
        result.videoTitle ||
        result.title ||
        "DSA Lesson";


    const summary =
        result.summary ||
        "No English summary was generated for this lesson.";


    const episodeNumber =
        extractEpisodeNumber(
            videoTitle
        );


    const hasOpenTarget =
        Boolean(
            result.video_id &&
            result.pattern
        );


    return (
        <article className="search-result">

            {/* ================================================= */}
            {/* RESULT SCORE */}
            {/* ================================================= */}

            <div className="search-result-score">
                {score || "—"}
            </div>


            <div className="search-result-content">

                {/* ================================================= */}
                {/* EPISODE */}
                {/* ================================================= */}

                <span className="ai-panel-label">

                    {episodeNumber
                        ? `EPISODE ${episodeNumber}`
                        : patternName}

                </span>


                {/* ================================================= */}
                {/* VIDEO TITLE */}
                {/* ================================================= */}

                <h3>
                    {videoTitle}
                </h3>


                {/* ================================================= */}
                {/* PATTERN */}
                {/* ================================================= */}

                <span className="ai-panel-label">
                    {patternName}
                </span>


                {/* ================================================= */}
                {/* TIMESTAMP */}
                {/* ================================================= */}

                {timestamp && (
                    <span className="ai-panel-label">

                        Exact timestamp ·{" "}
                        {timestamp}

                    </span>
                )}


                {/* ================================================= */}
                {/* ENGLISH SUMMARY */}
                {/* ================================================= */}

                <div className="search-result-summary">

                    <strong>
                        English Summary
                    </strong>

                    <p>
                        {summary}
                    </p>

                </div>


                {/* ================================================= */}
                {/* OPEN EXACT LESSON */}
                {/* ================================================= */}

                <button
                    className="primary-button"
                    onClick={() =>
                        onOpen?.(
                            result
                        )
                    }
                    disabled={
                        !hasOpenTarget
                    }
                >

                    {hasOpenTarget
                        ? "Open Exact Lesson →"
                        : "Lesson Unavailable"}

                </button>

            </div>

        </article>
    );
}