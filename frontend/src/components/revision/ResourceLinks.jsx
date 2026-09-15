export default function ResourceLinks({ resources = [] }) {
    if (!resources.length) return null;

    return (
        <section className="resource-section">
            <div className="section-heading">
                <span className="ai-panel-label">GO DEEPER</span>
                <h3>আরও Practice & Understanding</h3>
            </div>

            <div className="resource-grid">
                {resources.map((resource) => (
                    <a
                        key={resource.id || resource.url}
                        href={resource.url}
                        target="_blank"
                        rel="noreferrer"
                        className="resource-card"
                    >
                        <div className="resource-icon">
                            {resource.platform === "leetcode" ? "LC" : "GFG"}
                        </div>

                        <div>
                            <span>{resource.platform}</span>
                            <h4>{resource.title}</h4>
                            {resource.description && (
                                <p>{resource.description}</p>
                            )}
                        </div>

                        <span className="resource-arrow">↗</span>
                    </a>
                ))}
            </div>
        </section>
    );
}