import {
    useState,
} from "react";

import {
    useNavigate,
} from "react-router-dom";

import SearchBar from "../components/search/SearchBar";
import SearchResult from "../components/search/SearchResult";

import {
    searchDSA,
} from "../api/retrieval";

export default function Search() {
    const navigate =
        useNavigate();

    const [
        results,
        setResults,
    ] = useState([]);

    const [
        loading,
        setLoading,
    ] = useState(false);

    async function handleSearch(query) {
        if (!query.trim()) {
            return;
        }

        setLoading(true);

        try {
            const response =
                await searchDSA(query);

            setResults(
                response?.results || []
            );

        } catch (error) {
            console.error(
                "Search failed:",
                error
            );

            setResults([]);

        } finally {
            setLoading(false);
        }
    }

    function handleOpen(result) {
        if (
            !result?.patternId ||
            !result?.videoId
        ) {
            return;
        }

        navigate(
            `/pattern/${result.patternId}?video=${result.videoId}`
        );
    }

    return (
        <main className="search-page">

            <header className="search-header">

                <span className="hero-eyebrow">
                    AI SEARCH
                </span>

                <h1>
                    Find the exact lesson.
                </h1>

                <p>
                    যা বুঝতে চাইছো সেটা লিখো। AI knowledge
                    base থেকে exact pattern এবং video খুঁজে দেবে।
                </p>

            </header>

            <SearchBar
                onSearch={handleSearch}
            />

            {loading && (
                <div className="loading-card">
                    Searching your DSA knowledge base...
                </div>
            )}

            {!loading &&
                results.length > 0 && (
                    <section className="search-results">

                        {results.map(
                            (result, index) => (
                                <SearchResult
                                    key={
                                        result.id ||
                                        index
                                    }
                                    result={result}
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