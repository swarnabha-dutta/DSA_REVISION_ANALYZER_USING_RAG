import {
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    useLocation,
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

    const location =
        useLocation();


    /*
     * ========================================================
     * SEARCH / URL PARAMETERS
     * ========================================================
     *
     * Search can navigate to:
     *
     * /pattern/two-pointer?video=VIDEO_ID&t=183
     *
     * video = exact video requested by AI Search
     * t     = exact timestamp requested by AI Search
     */

    const searchParams =
        useMemo(
            () =>
                new URLSearchParams(
                    location.search
                ),
            [location.search]
        );


    const requestedVideoId =
        searchParams.get(
            "video"
        );


    const requestedTimestampRaw =
        searchParams.get("t");


    const requestedTimestamp =
        requestedTimestampRaw !== null
            ? Number(
                requestedTimestampRaw
            )
            : null;


    const hasRequestedTimestamp =
        Number.isFinite(
            requestedTimestamp
        ) &&
        requestedTimestamp >= 0;


    /*
     * ========================================================
     * PATTERN
     * ========================================================
     */

    const pattern =
        getPatternById(
            patternId
        );


    /*
     * ========================================================
     * STATE
     * ========================================================
     */

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


    const [
        loadError,
        setLoadError,
    ] = useState("");


    /*
     * ========================================================
     * SEARCH VIDEO NOT FOUND STATE
     * ========================================================
     *
     * If AI Search requests a video which does not belong
     * to the current pattern playlist, we must NOT silently
     * open the first video.
     */

    const [
        requestedVideoNotFound,
        setRequestedVideoNotFound,
    ] = useState(false);


    const {
        updateProgress,
        markCompleted,
        getVideoProgress,
    } = useVideoProgress();


    /*
     * ========================================================
     * LOAD VIDEOS FOR CURRENT PATTERN
     * ========================================================
     */

    useEffect(() => {
        let cancelled = false;


        async function loadVideos() {
            setLoading(true);
            setLoadError("");
            setRequestedVideoNotFound(false);


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
                 * ====================================================
                 * SELECT VIDEO
                 * ====================================================
                 *
                 * Priority:
                 *
                 * 1. Video requested from Search
                 * 2. First video in playlist
                 */

                if (
                    loadedVideos.length >
                    0
                ) {

                    const requestedVideo =
                        requestedVideoId
                            ? loadedVideos.find(
                                (video) =>
                                    String(
                                        video.id
                                    ) ===
                                    String(
                                        requestedVideoId
                                    )
                            )
                            : null;


                    /*
                     * =================================================
                     * EXACT VIDEO SAFETY
                     * =================================================
                     *
                     * Previously:
                     *
                     * requestedVideo || loadedVideos[0]
                     *
                     * This meant that an invalid video ID from Search
                     * silently opened the first lesson.
                     *
                     * That is incorrect for exact lesson navigation.
                     */

                    if (
                        requestedVideoId &&
                        !requestedVideo
                    ) {
                        setActiveVideo(
                            null
                        );

                        setActiveStartAt(
                            0
                        );

                        setRequestedVideoNotFound(
                            true
                        );

                        return;
                    }


                    setRequestedVideoNotFound(
                        false
                    );


                    const selectedVideo =
                        requestedVideo ||
                        loadedVideos[0];


                    const savedProgress =
                        getVideoProgress(
                            selectedVideo.id
                        );


                    setActiveVideo(
                        selectedVideo
                    );


                    /*
                     * =================================================
                     * START POSITION
                     * =================================================
                     *
                     * Priority:
                     *
                     * Search timestamp
                     *        ↓
                     * Saved progress
                     *        ↓
                     * Backend currentTime
                     *        ↓
                     * Zero
                     */

                    if (
                        requestedVideo &&
                        hasRequestedTimestamp
                    ) {
                        setActiveStartAt(
                            requestedTimestamp
                        );
                    } else {
                        setActiveStartAt(
                            savedProgress
                                ?.currentTime ||
                            selectedVideo.currentTime ||
                            0
                        );
                    }

                } else {

                    setActiveVideo(
                        null
                    );

                    setActiveStartAt(
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

                    setRequestedVideoNotFound(
                        false
                    );

                    setLoadError(
                        "Unable to load pattern videos."
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
        requestedVideoId,
        requestedTimestamp,
        hasRequestedTimestamp,
        getVideoProgress,
    ]);


    /*
     * ========================================================
     * MERGE VIDEO METADATA + LOCAL PROGRESS
     * ========================================================
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
     * ========================================================
     * ACTIVE VIDEO + LATEST PROGRESS
     * ========================================================
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
     * ========================================================
     * VIDEO PROGRESS
     * ========================================================
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
     * ========================================================
     * VIDEO COMPLETION
     * ========================================================
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
     * ========================================================
     * PLAYLIST VIDEO SELECTION
     * ========================================================
     */

    const handleVideoSelect =
        useCallback(
            (video) => {

                if (!video) {
                    return;
                }


                setActiveVideo(
                    video
                );


                /*
                 * When the user manually selects
                 * a video from the playlist, the
                 * Search timestamp must NOT be reused.
                 */

                const savedProgress =
                    getVideoProgress(
                        video.id
                    );


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
     * ========================================================
     * PATTERN NOT FOUND
     * ========================================================
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


    /*
     * ========================================================
     * PAGE
     * ========================================================
     */

    return (
        <main className="pattern-page">

            {/* ================================================= */}
            {/* PATTERN HEADER */}
            {/* ================================================= */}

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


            {/* ================================================= */}
            {/* LOADING */}
            {/* ================================================= */}

            {loading ? (

                <div className="loading-card">
                    Loading pattern playlist...
                </div>

            ) : loadError ? (

                <div className="loading-card">
                    {loadError}
                </div>

            ) : requestedVideoNotFound ? (

                <div className="loading-card">
                    Requested lesson was not found in this pattern playlist.
                </div>

            ) : videos.length ===
                0 ? (

                <div className="loading-card">
                    এই pattern-এর জন্য এখনো কোনো
                    video পাওয়া যায়নি।
                </div>

            ) : (

                <div className="learning-layout">

                    {/* ========================================= */}
                    {/* VIDEO AREA */}
                    {/* ========================================= */}

                    <section className="lesson-area">

                        <VideoPlayer
                            key={
                                activeVideoWithProgress?.id
                            }

                            video={
                                activeVideoWithProgress
                            }

                            /*
                             * This value comes from:
                             *
                             * Search timestamp
                             * OR saved progress
                             * OR zero
                             */

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


                        {/* ===================================== */}
                        {/* VIDEO INFORMATION */}
                        {/* ===================================== */}

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


                    {/* ========================================= */}
                    {/* PLAYLIST */}
                    {/* ========================================= */}

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