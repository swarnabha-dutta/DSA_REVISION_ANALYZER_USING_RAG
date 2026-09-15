export default function ProblemSet({
    problems = [],
    onStart,
}) {
    if (!problems.length) return null;

    return (
        <section className="problem-section">
            <div className="section-heading">
                <span className="ai-panel-label">APPLICATION</span>
                <h3>এবার নিজে Solve করো</h3>
                <p>
                    এই প্রশ্নগুলো ভিডিওর concept থেকে তৈরি। কোনো hint দেওয়া নেই।
                </p>
            </div>

            <div className="problem-list">
                {problems.map((problem, index) => (
                    <article className="problem-card" key={problem.id || index}>
                        <div className="problem-number">
                            {String(index + 1).padStart(2, "0")}
                        </div>

                        <div className="problem-content">
                            <div className="problem-meta">
                                <span>{problem.difficulty || "Medium"}</span>

                                {problem.topic && (
                                    <span>{problem.topic}</span>
                                )}
                            </div>

                            <h4>{problem.title}</h4>

                            <p>{problem.description}</p>

                            <button
                                className="secondary-button"
                                onClick={() => onStart?.(problem)}
                            >
                                Solve Problem →
                            </button>
                        </div>
                    </article>
                ))}
            </div>
        </section>
    );
}