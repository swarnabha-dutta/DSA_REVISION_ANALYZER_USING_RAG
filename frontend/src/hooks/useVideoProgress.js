import {
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";

const STORAGE_KEY =
    "dsa-video-progress";

/*
 * Load saved progress safely.
 */
function loadProgress() {
    try {
        const saved =
            localStorage.getItem(
                STORAGE_KEY
            );

        if (!saved) {
            return {};
        }

        const parsed =
            JSON.parse(saved);

        if (
            parsed &&
            typeof parsed === "object"
        ) {
            return parsed;
        }

        return {};
    } catch {
        return {};
    }
}

export default function useVideoProgress() {
    const [progress, setProgress] =
        useState(loadProgress);

    /*
     * Ref gives us access to the
     * latest progress without making
     * getVideoProgress recreate.
     */
    const progressRef =
        useRef(progress);

    /*
     * Update ref whenever React state changes.
     */
    useEffect(() => {
        progressRef.current =
            progress;
    }, [progress]);

    /*
     * Persist progress.
     */
    useEffect(() => {
        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(progress)
            );
        } catch (error) {
            console.error(
                "Unable to persist video progress:",
                error
            );
        }
    }, [progress]);

    /*
     * Update one video's progress.
     */
    const updateProgress =
        useCallback(
            (videoId, data) => {
                if (
                    !videoId ||
                    !data
                ) {
                    return;
                }

                setProgress(
                    (previous) => ({
                        ...previous,

                        [videoId]: {
                            ...(previous[
                                videoId
                            ] || {}),

                            ...data,
                        },
                    })
                );
            },
            []
        );

    /*
     * Mark video as completed.
     */
    const markCompleted =
        useCallback(
            (videoId) => {
                if (!videoId) {
                    return;
                }

                updateProgress(
                    videoId,
                    {
                        completed: true,

                        completedAt:
                            new Date()
                                .toISOString(),
                    }
                );
            },
            [updateProgress]
        );

    /*
     * Read saved progress.
     *
     * This callback stays stable.
     */
    const getVideoProgress =
        useCallback(
            (videoId) => {
                if (!videoId) {
                    return null;
                }

                return (
                    progressRef
                        .current[
                    videoId
                    ] || null
                );
            },
            []
        );

    return {
        progress,

        updateProgress,

        markCompleted,

        getVideoProgress,
    };
}