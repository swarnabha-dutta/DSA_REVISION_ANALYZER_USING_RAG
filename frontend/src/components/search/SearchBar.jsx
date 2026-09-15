import { useState } from "react";

export default function SearchBar({ onSearch }) {
    const [query, setQuery] = useState("");

    function handleSubmit(event) {
        event.preventDefault();

        if (!query.trim()) return;

        onSearch(query);
    }

    return (
        <form className="search-bar" onSubmit={handleSubmit}>
            <span className="search-icon">⌕</span>

            <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="e.g. How do I move two pointers when the sum is too large?"
            />

            <button type="submit">
                Search
            </button>
        </form>
    );
}