import { useState } from "react";

export default function AIChat({
    video,
    pattern,
    messages = [],
    onSend,
    onClose,
}) {
    const [input, setInput] = useState("");

    function handleSubmit(event) {
        event.preventDefault();

        const message = input.trim();

        if (!message) return;

        onSend(message);
        setInput("");
    }

    return (
        <aside className="ai-chat">
            <div className="ai-chat-header">
                <div className="ai-identity">
                    <div className="ai-avatar">✦</div>

                    <div>
                        <strong>DSA Revision AI</strong>
                        <span>{pattern?.name || "Concept Revision"}</span>
                    </div>
                </div>

                <button className="icon-button" onClick={onClose}>
                    ×
                </button>
            </div>

            <div className="ai-chat-context">
                <span>VIDEO COMPLETED</span>
                <p>{video?.title}</p>
            </div>

            <div className="ai-messages">
                {messages.length === 0 && (
                    <div className="ai-message ai-message-ai">
                        <strong>AI</strong>
                        <p>
                            দারুণ! ভিডিওটা শেষ করেছো। এবার দেখি concept টা তুমি আসলে কতটা
                            বুঝেছো।
                        </p>
                    </div>
                )}

                {messages.map((message, index) => (
                    <div
                        key={`${message.role}-${index}`}
                        className={`ai-message ${message.role === "user"
                                ? "ai-message-user"
                                : "ai-message-ai"
                            }`}
                    >
                        <strong>{message.role === "user" ? "You" : "AI"}</strong>
                        <p>{message.content}</p>
                    </div>
                ))}
            </div>

            <form className="ai-chat-input" onSubmit={handleSubmit}>
                <input
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    placeholder="AI-কে কিছু জিজ্ঞেস করো..."
                />

                <button type="submit">↑</button>
            </form>
        </aside>
    );
}