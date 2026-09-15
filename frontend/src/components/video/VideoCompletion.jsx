import {
    useEffect,
    useRef,
} from "react";

const COMPLETION_THRESHOLD_SECONDS = 8;

export default function VideoCompletion({
    videoId,
    duration,
    currentTime,
    completed,
    onComplete,
}) {
    const triggered =
        useRef(false);

    /*
     * Reset completion trigger
     * when switching to another video.
     */
    useEffect(() => {
        triggered.current = false;
    }, [videoId]);

    /*
     * Detect completion when the learner
     * enters the final 8 seconds.
     */
    useEffect(() => {
        if (
            completed ||
            triggered.current
        ) {
            return;
        }

        if (
            !duration ||
            currentTime < 0
        ) {
            return;
        }

        const remaining =
            duration - currentTime;

        if (
            remaining <=
            COMPLETION_THRESHOLD_SECONDS
        ) {
            triggered.current = true;

            onComplete?.();
        }
    }, [
        duration,
        currentTime,
        completed,
        onComplete,
    ]);

    /*
     * This component is intentionally
     * UI-less.
     */
    return null;
}