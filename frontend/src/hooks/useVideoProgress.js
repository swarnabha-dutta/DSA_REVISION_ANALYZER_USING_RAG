import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "dsa-video-progress";

function loadProgress() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);

        return saved ? JSON.parse(saved) : {};
    } catch {
        return {};
    }
}

export default function useVideoProgress() {
    const [progress, setProgress] = useState(loadProgress);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
    }, [progress]);

    const updateProgress = useCallback((videoId, data) => {
        if (!videoId) return;

        setProgress((previous) => ({
            ...previous,
            [videoId]: {
                ...(previous[videoId] || {}),
                ...data,
            },
        }));
    }, []);

    const markCompleted = useCallback(
        (videoId) => {
            updateProgress(videoId, {
                completed: true,
                completedAt: new Date().toISOString(),
            });
        },
        [updateProgress]
    );

    const getVideoProgress = useCallback(
        (videoId) => {
            return progress[videoId] || null;
        },
        [progress]
    );

    return {
        progress,
        updateProgress,
        markCompleted,
        getVideoProgress,
    };
}