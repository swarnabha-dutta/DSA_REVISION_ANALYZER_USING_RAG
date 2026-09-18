import { useState } from "react";
import { useNavigate } from "react-router-dom";

import SearchBar from "../components/search/SearchBar";
import SearchResult from "../components/search/SearchResult";
import { getPatternById } from "../data/patterns";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function Search() {
    const navigate = useNavigate();

    const [results, setResults] = useState([]);
    const [answer, setAnswer] = useState("");
    const [responseLanguage, setResponseLanguage] =
        useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSearch(query) {
        if (!query.trim()) {
            return;
        }

        setLoading(true);
        setError("");
        setAnswer("");
        setResponseLanguage("");
        setResults([]);

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/rag/query`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body: JSON.stringify({
                        query: query.trim(),

                        /*
                         * Retrieve more chunks so that
                         * multiple relevant videos have a
                         * chance to appear.
                         */
                        top_k: 12,
                    }),
                }
            );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data?.detail ||
                    "AI search failed."
                );
            }

            setAnswer(
                data?.answer || ""
            );

            setResponseLanguage(
                data?.response_language || ""
            );

            setResults(
                groupResultsByVideo(
                    data?.sources || []
                )
            );

        } catch (searchError) {

            console.error(
                "AI search failed:",
                searchError
            );

            setError(
                searchError?.message ||
                "Something went wrong while searching."
            );

            setResults([]);

        } finally {
            setLoading(false);
        }
    }


    // ========================================================
    // EPISODE NUMBER
    // ========================================================

    function extractEpisodeNumber(title) {
        if (!title) {
            return Number.POSITIVE_INFINITY;
        }

        const match = String(title).match(
            /episode\s*[-:]?\s*(\d+)/i
        );

        if (!match) {
            return Number.POSITIVE_INFINITY;
        }

        return Number(
            match[1]
        );
    }


    // ========================================================
    // GROUP RESULTS BY VIDEO
    // ========================================================

    function groupResultsByVideo(sources) {
        const groups = new Map();

        for (const source of sources || []) {

            const videoId = String(
                source?.video_id || ""
            ).trim();

            /*
             * We need video_id internally for
             * exact lesson navigation.
             */
            if (!videoId) {
                continue;
            }

            if (!groups.has(videoId)) {

                groups.set(
                    videoId,
                    {
                        ...source,

                        video_id: videoId,

                        summary:
                            source?.summary || "",

                        supportingChunks: [],
                    }
                );
            }

            const group =
                groups.get(videoId);

            group.supportingChunks.push(
                source
            );


            // ------------------------------------------------
            // Summary fallback
            // ------------------------------------------------

            if (
                !group.summary &&
                source?.summary
            ) {
                group.summary =
                    source.summary;
            }


            // ------------------------------------------------
            // Video title fallback
            // ------------------------------------------------

            if (
                !group.video_title &&
                source?.video_title
            ) {
                group.video_title =
                    source.video_title;
            }


            // ------------------------------------------------
            // Keep highest-ranked chunk
            // ------------------------------------------------

            const currentRank =
                Number(group.rank);

            const sourceRank =
                Number(source?.rank);

            if (
                Number.isFinite(
                    sourceRank
                ) &&
                (
                    !Number.isFinite(
                        currentRank
                    ) ||
                    sourceRank <
                    currentRank
                )
            ) {

                group.rank =
                    sourceRank;

                group.timestamp_start =
                    source.timestamp_start;

                group.timestamp_end =
                    source.timestamp_end;

                group.point_id =
                    source.point_id;
            }
        }


        // ====================================================
        // SORT
        // ====================================================

        return Array.from(
            groups.values()
        ).sort(
            (a, b) => {

                const episodeA =
                    extractEpisodeNumber(
                        a.video_title
                    );

                const episodeB =
                    extractEpisodeNumber(
                        b.video_title
                    );

                if (
                    episodeA !==
                    episodeB
                ) {
                    return (
                        episodeA -
                        episodeB
                    );
                }

                return (
                    Number(
                        a.rank ||
                        999999
                    ) -
                    Number(
                        b.rank ||
                        999999
                    )
                );
            }
        );
    }


    // ========================================================
    // EXACT LESSON OPEN
    // ========================================================

    function handleOpen(result) {

        if (
            !result?.pattern ||
            !result?.video_id
        ) {
            return;
        }


        // ----------------------------------------------------
        // Resolve canonical pattern
        // ----------------------------------------------------

        const pattern =
            getPatternById(
                result.pattern
            );

        if (!pattern) {

            console.error(
                "Cannot open search result: unknown pattern",
                result.pattern
            );

            return;
        }


        // ----------------------------------------------------
        // Video ID
        // ----------------------------------------------------

        const videoId =
            String(
                result.video_id
            ).trim();

        if (!videoId) {
            return;
        }


        // ----------------------------------------------------
        // Timestamp
        // ----------------------------------------------------

        const timestamp =
            Number(
                result.timestamp_start
            );

        const hasTimestamp =
            Number.isFinite(
                timestamp
            ) &&
            timestamp >= 0;


        // ----------------------------------------------------
        // URL
        // ----------------------------------------------------

        const searchParams =
            new URLSearchParams();

        searchParams.set(
            "video",
            videoId
        );

        if (hasTimestamp) {

            searchParams.set(
                "t",
                String(
                    Math.floor(
                        timestamp
                    )
                )
            );
        }


        // ----------------------------------------------------
        // Navigate
        // ----------------------------------------------------

        navigate(
            `/pattern/${pattern.id}?${searchParams.toString()}`
        );
    }


    return (
        <main className="search-page">

            {/* ================================================= */}
            {/* HEADER */}
            {/* ================================================= */}

            <header className="search-header">

                <span className="hero-eyebrow">
                    AI SEARCH
                </span>

                <h1>
                    Find the exact lesson.
                </h1>

                <p>
                    যা বুঝতে চাইছো সেটা লিখো।
                    AI knowledge base থেকে grounded
                    answer এবং exact lesson খুঁজে দেবে।
                </p>

            </header>


            {/* ================================================= */}
            {/* SEARCH BAR */}
            {/* ================================================= */}

            <SearchBar
                onSearch={handleSearch}
            />


            {/* ================================================= */}
            {/* LOADING */}
            {/* ================================================= */}

            {loading && (
                <div className="loading-card">
                    Searching your DSA knowledge base
                    and generating an AI answer...
                </div>
            )}


            {/* ================================================= */}
            {/* ERROR */}
            {/* ================================================= */}

            {!loading &&
                error && (
                    <div className="loading-card">
                        {error}
                    </div>
                )}


            {/* ================================================= */}
            {/* AI ANSWER */}
            {/* ================================================= */}

            {!loading &&
                answer && (
                    <section className="ai-answer-card">

                        <div className="hero-eyebrow">

                            AI REVISION

                            {responseLanguage
                                ? ` · ${responseLanguage}`
                                : ""}

                        </div>

                        <div className="ai-answer">
                            {answer}
                        </div>

                    </section>
                )}


            {/* ================================================= */}
            {/* VIDEO RESULTS */}
            {/* ================================================= */}

            {!loading &&
                results.length > 0 && (
                    <section className="search-results">

                        {results.map(
                            (
                                result,
                                index
                            ) => (

                                <SearchResult
                                    key={
                                        result.video_id ||
                                        result.point_id ||
                                        index
                                    }

                                    result={
                                        result
                                    }

                                    onOpen={
                                        handleOpen
                                    }
                                />
                            )
                        )}

                    </section>
                )}

        </main>
    );
}