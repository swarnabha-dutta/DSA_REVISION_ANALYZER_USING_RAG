export default function SearchResult({
    result,
    onOpen,
}) {
    if (!result) return null;

    return (
        <article className="search-result">
            <div className="search-result-score">
                {Math.round((result.score || 0) * 100)}%
            </div>

            <div className="search-result-content">
                <span className="ai-panel-label">
                    {result.patternName || "DSA VIDEO"}
                </span>

                <h3>{result.videoTitle}</h3>

                {result.snippet && <p>{result.snippet}</p>}

                <button
                    className="primary-button"
                    onClick={() => onOpen(result)}
                >
                    Open Exact Lesson →
                </button>
            </div>
        </article>
    );
}