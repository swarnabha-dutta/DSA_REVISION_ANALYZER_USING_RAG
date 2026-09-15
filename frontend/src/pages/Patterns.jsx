import PatternGrid from "../components/patterns/PatternGrid";

import {
    PROJECT_STATS,
    patterns,
} from "../data/patterns";

import "../styles/patterns.css";

export default function Patterns() {
    return (
        <main className="patterns-page">

            <header className="patterns-header">

                <span className="hero-eyebrow">
                    DSA PATTERNS
                </span>

                <h1>
                    Choose a pattern.
                </h1>

                <p>
                    Start a focused learning path, watch the
                    lessons in order, and revise each concept
                    with AI after completing a video.
                </p>

            </header>

            <div className="patterns-summary">

                <div>
                    <strong>
                        {PROJECT_STATS.patterns}
                    </strong>

                    <span>
                        Patterns
                    </span>
                </div>

                <div>
                    <strong>
                        {PROJECT_STATS.videos}
                    </strong>

                    <span>
                        Videos
                    </span>
                </div>

                <div>
                    <strong>
                        {PROJECT_STATS.system}
                    </strong>

                    <span>
                        Revision system
                    </span>
                </div>

            </div>

            <PatternGrid
                patterns={patterns}
            />

        </main>
    );
}