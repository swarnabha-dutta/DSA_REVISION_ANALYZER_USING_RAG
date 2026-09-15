import {
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";

import { resolveVideoId } from "../../lib/videoUtils";
import VideoCompletion from "./VideoCompletion";

const YOUTUBE_API_SRC =
    "https://www.youtube.com/iframe_api";

let youtubeApiPromise = null;

/*
 * Load the YouTube IFrame Player API only once.
 */
function loadYoutubeApi() {
    if (window.YT?.Player) {
        return Promise.resolve(window.YT);
    }

    if (youtubeApiPromise) {
        return youtubeApiPromise;
    }

    youtubeApiPromise = new Promise((resolve) => {
        const previousCallback =
            window.onYouTubeIframeAPIReady;

        window.onYouTubeIframeAPIReady = () => {
            previousCallback?.();
            resolve(window.YT);
        };

        const existingScript =
            document.querySelector(
                `script[src="${YOUTUBE_API_SRC}"]`
            );

        if (!existingScript) {
            const script =
                document.createElement("script");

            script.src = YOUTUBE_API_SRC;
            script.async = true;

            document.head.appendChild(script);
        }
    });

    return youtubeApiPromise;
}

/*
 * Convert any invalid number into a safe
 * non-negative video time value.
 */
function normalizeTime(value) {
    const number = Number(value);

    if (!Number.isFinite(number) || number < 0) {
        return 0;
    }

    return number;
}

export default function VideoPlayer({
    video,
    startAt = 0,
    onProgress,
    onComplete,
}) {
    const containerRef = useRef(null);
    const playerRef = useRef(null);
    const progressTimerRef = useRef(null);

    /*
     * Keep callback references current without
     * forcing the YouTube player to recreate.
     */
    const onProgressRef =
        useRef(onProgress);

    const onCompleteRef =
        useRef(onComplete);

    const completedRef =
        useRef(Boolean(video?.completed));

    const fallbackDurationRef =
        useRef(
            normalizeTime(video?.duration)
        );

    const [currentTime, setCurrentTime] =
        useState(
            normalizeTime(startAt)
        );

    const [duration, setDuration] =
        useState(
            normalizeTime(video?.duration)
        );

    const videoId =
        resolveVideoId(video);

    /*
     * Keep latest callbacks available.
     */
    useEffect(() => {
        onProgressRef.current =
            onProgress;
    }, [onProgress]);

    useEffect(() => {
        onCompleteRef.current =
            onComplete;
    }, [onComplete]);

    /*
     * Keep completion state current.
     */
    useEffect(() => {
        completedRef.current =
            Boolean(video?.completed);
    }, [video?.completed]);

    /*
     * Keep backend duration as fallback.
     */
    useEffect(() => {
        fallbackDurationRef.current =
            normalizeTime(
                video?.duration
            );
    }, [video?.duration]);

    /*
     * Stop progress polling.
     */
    const stopProgressPolling =
        useCallback(() => {
            if (progressTimerRef.current) {
                window.clearInterval(
                    progressTimerRef.current
                );

                progressTimerRef.current =
                    null;
            }
        }, []);

    /*
     * Read current progress directly
     * from the YouTube player.
     */
    const syncProgress =
        useCallback(() => {
            const player =
                playerRef.current;

            if (!player?.getCurrentTime) {
                return;
            }

            const time =
                normalizeTime(
                    player.getCurrentTime()
                );

            const playerDuration =
                normalizeTime(
                    player.getDuration?.()
                );

            const safeDuration =
                playerDuration > 0
                    ? playerDuration
                    : fallbackDurationRef.current;

            setCurrentTime(time);

            if (safeDuration > 0) {
                setDuration(
                    safeDuration
                );
            }

            onProgressRef.current?.({
                currentTime: time,
                duration: safeDuration,
            });
        }, []);

    /*
     * Start polling while the video is playing.
     */
    const startProgressPolling =
        useCallback(() => {
            stopProgressPolling();

            syncProgress();

            progressTimerRef.current =
                window.setInterval(
                    syncProgress,
                    2000
                );
        }, [
            stopProgressPolling,
            syncProgress,
        ]);

    /*
     * Create the YouTube player.
     *
     * IMPORTANT:
     * This effect depends on videoId + startAt,
     * not on current progress.
     *
     * Therefore a progress update will NOT
     * recreate the YouTube player.
     */
    useEffect(() => {
        if (
            !videoId ||
            !containerRef.current
        ) {
            return undefined;
        }

        let cancelled = false;

        const initialStartAt =
            normalizeTime(startAt);

        setCurrentTime(
            initialStartAt
        );

        setDuration(
            normalizeTime(
                video?.duration
            )
        );

        async function initializePlayer() {
            const YT =
                await loadYoutubeApi();

            if (
                cancelled ||
                !containerRef.current
            ) {
                return;
            }

            stopProgressPolling();

            /*
             * Destroy any previous player.
             */
            playerRef.current?.destroy?.();

            /*
             * Create new YouTube player.
             */
            playerRef.current =
                new YT.Player(
                    containerRef.current,
                    {
                        videoId,

                        playerVars: {
                            autoplay: 0,
                            rel: 0,
                            modestbranding: 1,
                            playsinline: 1,

                            start: Math.floor(
                                initialStartAt
                            ),
                        },

                        events: {
                            /*
                             * Player ready.
                             */
                            onReady(event) {
                                const player =
                                    event.target;

                                const playerDuration =
                                    normalizeTime(
                                        player.getDuration?.()
                                    );

                                if (
                                    playerDuration > 0
                                ) {
                                    fallbackDurationRef.current =
                                        playerDuration;

                                    setDuration(
                                        playerDuration
                                    );
                                }

                                /*
                                 * Resume from saved position.
                                 */
                                if (
                                    initialStartAt > 0
                                ) {
                                    player.seekTo(
                                        initialStartAt,
                                        true
                                    );
                                }

                                syncProgress();
                            },

                            /*
                             * Player state changed.
                             */
                            onStateChange(event) {
                                /*
                                 * PLAYING
                                 */
                                if (
                                    event.data ===
                                    YT.PlayerState.PLAYING
                                ) {
                                    startProgressPolling();

                                    return;
                                }

                                /*
                                 * PAUSED / BUFFERING /
                                 * CUED / ENDED
                                 */
                                syncProgress();

                                /*
                                 * Actual video ended.
                                 */
                                if (
                                    event.data ===
                                    YT.PlayerState.ENDED &&
                                    !completedRef.current
                                ) {
                                    stopProgressPolling();

                                    const endedDuration =
                                        normalizeTime(
                                            event.target.getDuration?.()
                                        ) ||
                                        fallbackDurationRef.current;

                                    if (
                                        endedDuration > 0
                                    ) {
                                        setDuration(
                                            endedDuration
                                        );

                                        setCurrentTime(
                                            endedDuration
                                        );
                                    }

                                    onCompleteRef.current?.();
                                }
                            },
                        },
                    }
                );
        }

        initializePlayer();

        /*
         * Cleanup when video changes
         * or component unmounts.
         */
        return () => {
            cancelled = true;

            stopProgressPolling();

            playerRef.current?.destroy?.();

            playerRef.current =
                null;
        };
    }, [
        videoId,
        startAt,
        stopProgressPolling,
        startProgressPolling,
        syncProgress,
        video?.duration,
    ]);

    /*
     * No valid YouTube ID.
     */
    if (!videoId) {
        return (
            <div className="video-placeholder">
                <span>VIDEO</span>

                <p>
                    এই ভিডিওর YouTube ID পাওয়া যায়নি।
                </p>
            </div>
        );
    }

    return (
        <div className="video-player-shell">
            <div className="video-player">
                <div
                    ref={containerRef}
                    className="youtube-player"
                />
            </div>

            <VideoCompletion
                videoId={videoId}
                duration={duration}
                currentTime={currentTime}
                completed={
                    video?.completed
                }
                onComplete={
                    onComplete
                }
            />
        </div>
    );
}