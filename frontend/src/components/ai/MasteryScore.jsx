export default function MasteryScore({
    score = 0,
    label = "Concept Mastery",
}) {
    const normalizedScore = Math.min(100, Math.max(0, Number(score) || 0));

    let status = "Needs Work";

    if (normalizedScore >= 80) {
        status = "Strong";
    } else if (normalizedScore >= 60) {
        status = "Developing";
    }

    return (
        <section className="mastery-card">
            <div className="mastery-top">
                <div>
                    <span className="ai-panel-label">UNDERSTANDING</span>
                    <h3>{label}</h3>
                </div>

                <strong className="mastery-number">
                    {normalizedScore}%
                </strong>
            </div>

            <div className="mastery-track">
                <div
                    className="mastery-fill"
                    style={{
                        width: `${normalizedScore}%`,
                    }}
                />
            </div>

            <div className="mastery-bottom">
                <span>{status}</span>

                <span>
                    {normalizedScore < 70
                        ? "আরও revision দরকার"
                        : "ভালো grasp তৈরি হয়েছে"}
                </span>
            </div>
        </section>
    );
}