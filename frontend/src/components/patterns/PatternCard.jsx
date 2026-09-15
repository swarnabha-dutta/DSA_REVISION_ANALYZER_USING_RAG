import { Link } from "react-router-dom";

export default function PatternCard({ pattern }) {
    return (
        <Link
            to={`/pattern/${pattern.id}`}
            className="pattern-card"
        >
            <div className="pattern-card-top">
                <span className="pattern-card-category">
                    {pattern.category}
                </span>

                <span className="pattern-card-difficulty">
                    {pattern.difficulty}
                </span>
            </div>

            <h3>{pattern.name}</h3>

            <p>{pattern.description}</p>

            <div className="pattern-card-footer">
                <span>
                    {pattern.videoCount > 0
                        ? `${pattern.videoCount} videos`
                        : "Start learning"}
                </span>

                <span aria-hidden="true">→</span>
            </div>
        </Link>
    );
}