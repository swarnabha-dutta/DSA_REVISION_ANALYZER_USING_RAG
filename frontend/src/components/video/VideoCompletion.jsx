import { useEffect, useRef } from "react";

export default function VideoCompletion({
    duration,
    currentTime,
    completed,
    onComplete,
}) {
    const triggered = useRef(false);

    useEffect(() => {
        if (!duration || !currentTime) return;

        const remaining = duration - currentTime;

        // Consider the video complete when the user reaches
        // the final 8 seconds.
        if (remaining <= 8 && !triggered.current) {
            triggered.current = true;

            if (!completed) {
                onComplete();
            }
        }
    }, [duration, currentTime, completed, onComplete]);

    return null;
}