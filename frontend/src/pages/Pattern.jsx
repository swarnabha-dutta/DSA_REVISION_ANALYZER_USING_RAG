import {
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    useNavigate,
    useParams,
} from "react-router-dom";

import VideoPlayer from "../components/video/VideoPlayer";

import VideoPlaylist from "../components/patterns/VideoPlaylist";

import {
    getPatternById,
} from "../data/patterns";

import {
    getPatternVideos,
} from "../api/client";

import useVideoProgress from "../hooks/useVideoProgress";

export default function Pattern() {
    const {
        patternId,
    } = useParams();

    const navigate =
        useNavigate();

    const pattern =
        getPatternById(
            patternId
        );

    const [
        videos,
        setVideos,
    ] = useState([]);

    const [
        activeVideo,
        setActiveVideo,
    ] = useState(null);

    /*
     * IMPORTANT:
     *
     * activeStartAt represents the
     * position from which the selected
     * video should initially start.
     *
     * It should NOT update every 2 sec
     * when progress is saved.
     */
    const [
        activeStartAt,
        setActiveStartAt,
    ] = useState(0);

    const [
        loading,
        setLoading,
    ] = useState(true);

    const {
        updateProgress,
        markCompleted,
        getVideoProgress,
    } = useVideoProgress();

    /*
     * Load videos for the current pattern.
     */
    useEffect(() => {
        let cancelled = false;

        async function loadVideos() {
            setLoading(true);

            try {
                const response =
                    await getPatternVideos(
                        patternId
                    );

                const loadedVideos =
                    response?.videos ||
                    [];

                if (cancelled) {
                    return;
                }

                setVideos(
                    loadedVideos
                );

                /*
                 * Automatically select
                 * the first video.
                 */
                if (
                    loadedVideos.length >
                    0
                ) {
                    const firstVideo =
                        loadedVideos[0];

                    const savedProgress =
                        getVideoProgress(
                            firstVideo.id
                        );

                    setActiveVideo(
                        firstVideo
                    );

                    /*
                     * Resume from previous
                     * position if available.
                     */
                    setActiveStartAt(
                        savedProgress
                            ?.currentTime ||
                        0
                    );
                }
            } catch (error) {
                console.error(
                    "Unable to load pattern videos:",
                    error
                );

                if (!cancelled) {
                    setVideos([]);

                    setActiveVideo(
                        null
                    );

                    setActiveStartAt(
                        0
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoading(
                        false
                    );
                }
            }
        }

        loadVideos();

        return () => {
            cancelled = true;
        };
    }, [
        patternId,
        getVideoProgress,
    ]);

    /*
     * Merge backend video metadata
     * with local learning progress.
     */
    const videosWithProgress =
        useMemo(
            () =>
                videos.map(
                    (video) => {
                        const saved =
                            getVideoProgress(
                                video.id
                            );

                        return {
                            ...video,

                            completed:
                                saved?.completed ??
                                video.completed ??
                                false,

                            currentTime:
                                saved?.currentTime ??
                                0,
                        };
                    }
                ),
            [
                videos,
                getVideoProgress,
            ]
        );

    /*
     * Get active video with
     * latest progress information.
     */
    const activeVideoWithProgress =
        useMemo(() => {
            if (!activeVideo) {
                return null;
            }

            return (
                videosWithProgress.find(
                    (video) =>
                        video.id ===
                        activeVideo.id
                ) ||
                activeVideo
            );
        }, [
            activeVideo,
            videosWithProgress,
        ]);

    /*
     * Receive progress from
     * the YouTube player.
     */
    const handleProgress =
        useCallback(
            ({
                currentTime,
                duration,
            }) => {
                const videoId =
                    activeVideo?.id;

                if (!videoId) {
                    return;
                }

                updateProgress(
                    videoId,
                    {
                        currentTime,

                        duration,

                        updatedAt:
                            new Date()
                                .toISOString(),
                    }
                );
            },
            [
                activeVideo?.id,
                updateProgress,
            ]
        );

    /*
     * Video completion.
     */
    const handleVideoComplete =
        useCallback(() => {
            const videoId =
                activeVideo?.id;

            if (!videoId) {
                return;
            }

            /*
             * Save completion state.
             */
            markCompleted(
                videoId
            );

            /*
             * Open AI revision.
             */
            navigate(
                `/revision/${videoId}`
            );
        }, [
            activeVideo?.id,
            markCompleted,
            navigate,
        ]);

    /*
     * User selects another video
     * from the playlist.
     */
    const handleVideoSelect =
        useCallback(
            (video) => {
                setActiveVideo(
                    video
                );

                /*
                 * Find saved progress
                 * for selected video.
                 */
                const savedProgress =
                    getVideoProgress(
                        video.id
                    );

                /*
                 * Player starts from:
                 *
                 * saved progress
                 * OR backend currentTime
                 * OR zero
                 */
                setActiveStartAt(
                    savedProgress
                        ?.currentTime ||
                    video.currentTime ||
                    0
                );
            },
            [
                getVideoProgress,
            ]
        );

    /*
     * Pattern not found.
     */
    if (!pattern) {
        return (
            <main className="page-content">
                <div className="loading-card">
                    Pattern not found.
                </div>
            </main>
        );
    }

    return (
        <main className="pattern-page">
            {/* =========================
                PATTERN HEADER
               ========================= */}

            <header className="pattern-header">
                <span className="hero-eyebrow">
                    PATTERN
                </span>

                <h1>
                    {pattern.name}
                </h1>

                <p>
                    {
                        pattern.description
                    }
                </p>
            </header>

            {/* =========================
                LOADING
               ========================= */}

            {loading ? (
                <div className="loading-card">
                    Loading pattern playlist...
                </div>
            ) : videos.length ===
                0 ? (
                <div className="loading-card">
                    এই pattern-এর জন্য এখনো কোনো
                    video পাওয়া যায়নি।
                </div>
            ) : (
                <div className="learning-layout">
                    {/* =========================
                        VIDEO AREA
                       ========================= */}

                    <section className="lesson-area">
                        <VideoPlayer
                            key={
                                activeVideoWithProgress?.id
                            }
                            video={
                                activeVideoWithProgress
                            }
                            startAt={
                                activeStartAt
                            }
                            onProgress={
                                handleProgress
                            }
                            onComplete={
                                handleVideoComplete
                            }
                        />

                        {/* =========================
                            VIDEO INFORMATION
                           ========================= */}

                        {activeVideoWithProgress && (
                            <div className="lesson-info">
                                <span>
                                    NOW LEARNING
                                </span>

                                <h2>
                                    {
                                        activeVideoWithProgress.title
                                    }
                                </h2>

                                <p>
                                    {
                                        activeVideoWithProgress.description ||
                                        "এই lesson-এর concept গভীরভাবে বুঝে নাও।"
                                    }
                                </p>
                            </div>
                        )}
                    </section>

                    {/* =========================
                        PLAYLIST
                       ========================= */}

                    <VideoPlaylist
                        videos={
                            videosWithProgress
                        }
                        activeVideoId={
                            activeVideoWithProgress?.id
                        }
                        onSelect={
                            handleVideoSelect
                        }
                    />
                </div>
            )}
        </main>
    );
}