import { useState } from "react";
import { useNavigate } from "react-router-dom";

import SearchBar from "../components/search/SearchBar";
import SearchResult from "../components/search/SearchResult";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function Search() {
    const navigate = useNavigate();

    const [results, setResults] = useState([]);
    const [answer, setAnswer] = useState("");
    const [responseLanguage, setResponseLanguage] = useState("");
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
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify({
                        query: query.trim(),
                        top_k: 5,
                    }),
                }
            );

            const data = await response.json();

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
                data?.sources || []
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


    function handleOpen(result) {
        if (
            !result?.pattern ||
            !result?.video_id
        ) {
            return;
        }

        const timestamp = Number(
            result?.timestamp_start
        );

        const hasTimestamp =
            Number.isFinite(timestamp) &&
            timestamp >= 0;

        const videoQuery = hasTimestamp
            ? `?video=${result.video_id}&t=${Math.floor(timestamp)}`
            : `?video=${result.video_id}`;

        navigate(
            `/pattern/${result.pattern}${videoQuery}`
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

            {!loading && error && (
                <div className="loading-card">
                    {error}
                </div>
            )}


            {/* ================================================= */}
            {/* AI ANSWER */}
            {/* ================================================= */}

            {!loading && answer && (
                <section className="ai-answer-card">

                    <div className="hero-eyebrow">

                        AI REVISION

                        {responseLanguage
                            ? ` · ${responseLanguage}`
                            : ""
                        }

                    </div>

                    <div className="ai-answer">
                        {answer}
                    </div>

                </section>
            )}


            {/* ================================================= */}
            {/* SOURCES */}
            {/* ================================================= */}

            {!loading &&
                results.length > 0 && (
                    <section className="search-results">

                        {results.map(
                            (result, index) => (

                                <SearchResult
                                    key={
                                        result.point_id ||
                                        result.id ||
                                        index
                                    }

                                    result={{
                                        ...result,

                                        id:
                                            result.point_id,

                                        patternId:
                                            result.pattern,

                                        videoId:
                                            result.video_id,

                                        timestampStart:
                                            result.timestamp_start,

                                        timestampEnd:
                                            result.timestamp_end,
                                    }}

                                    onOpen={
                                        handleOpen
                                    }
                                />

                            )
                        )}

                    </section>
                )
            }

        </main>
    );
}