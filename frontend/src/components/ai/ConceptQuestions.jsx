import { useState } from "react";

export default function ConceptQuestions({
    questions = [],
    onSubmit,
    loading = false,
}) {
    const [answer, setAnswer] = useState("");

    const currentQuestion = questions[0];

    if (loading) {
        return (
            <div className="ai-panel">
                <div className="ai-loading">
                    <span className="ai-orb" />
                    <div>
                        <strong>AI ভাবছে...</strong>
                        <p>এই ভিডিওর concept থেকে তোমার জন্য প্রশ্ন তৈরি হচ্ছে।</p>
                    </div>
                </div>
            </div>
        );
    }

    if (!currentQuestion) {
        return (
            <div className="ai-panel ai-empty">
                <span className="ai-panel-label">AI REVISION</span>
                <h3>Concept revision ready.</h3>
                <p>এই ভিডিওর গভীর understanding যাচাই করার জন্য AI প্রশ্ন করবে।</p>
            </div>
        );
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (!answer.trim()) return;

        onSubmit({
            questionId: currentQuestion.id,
            question: currentQuestion.question,
            answer: answer.trim(),
        });

        setAnswer("");
    }

    return (
        <section className="ai-panel">
            <div className="ai-panel-header">
                <div>
                    <span className="ai-panel-label">AI CONCEPT CHECK</span>
                    <h3>ভিডিওটা সত্যিই বুঝেছো তো?</h3>
                </div>

                <div className="question-count">
                    প্রশ্ন 1 / {questions.length}
                </div>
            </div>

            <div className="concept-question">
                <span>প্রশ্ন</span>

                <p>{currentQuestion.question}</p>
            </div>

            <form onSubmit={handleSubmit}>
                <textarea
                    value={answer}
                    onChange={(event) => setAnswer(event.target.value)}
                    placeholder="নিজের ভাষায় উত্তর দাও..."
                    rows={6}
                />

                <button
                    className="primary-button"
                    type="submit"
                    disabled={!answer.trim()}
                >
                    উত্তর জমা দাও →
                </button>
            </form>
        </section>
    );
}