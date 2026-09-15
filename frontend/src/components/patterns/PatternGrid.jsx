import PatternCard from "./PatternCard";

export default function PatternGrid({ patterns = [] }) {
    if (!patterns.length) {
        return (
            <div className="loading-card">
                No DSA patterns are available yet.
            </div>
        );
    }

    return (
        <section
            className="pattern-grid"
            aria-label="DSA patterns"
        >
            {patterns.map((pattern) => (
                <PatternCard
                    key={pattern.id}
                    pattern={pattern}
                />
            ))}
        </section>
    );
}