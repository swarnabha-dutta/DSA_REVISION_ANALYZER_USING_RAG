const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    if (!response.ok) {
        const message = await response.text();

        throw new Error(message || `API error: ${response.status}`);
    }

    return response.json();
}

export async function searchKnowledge(query) {
    return request("/api/search", {
        method: "POST",
        body: JSON.stringify({
            query,
        }),
    });
}

export async function getPatternVideos(patternId) {
    return request(`/api/patterns/${patternId}/videos`);
}

export async function getVideo(videoId) {
    return request(`/api/videos/${videoId}`);
}

export async function generateRevisionQuestions(payload) {
    return request("/api/revision/questions", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function evaluateRevisionAnswer(payload) {
    return request("/api/revision/evaluate", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function generatePracticeProblems(payload) {
    return request("/api/revision/problems", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function getLearningResources(payload) {
    return request("/api/revision/resources", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}