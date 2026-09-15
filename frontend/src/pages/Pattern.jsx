import {
    useEffect,
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

export default function Pattern() {
    const {
        patternId,
    } = useParams();

    const navigate = useNavigate();

    const pattern =
        getPatternById(patternId);

    const [
        videos,
        setVideos,
    ] = useState([]);

    const [
        activeVideo,
        setActiveVideo,
    ] = useState(null);

    const [
        loading,
        setLoading,
    ] = useState(true);

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
                    response?.videos || [];

                if (cancelled) {
                    return;
                }

                setVideos(
                    loadedVideos
                );

                if (
                    loadedVideos.length > 0
                ) {
                    setActiveVideo(
                        loadedVideos[0]
                    );
                }

            } catch (error) {
                console.error(
                    "Unable to load pattern videos:",
                    error
                );

                if (!cancelled) {
                    setVideos([]);
                    setActiveVideo(null);
                }

            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        loadVideos();

        return () => {
            cancelled = true;
        };
    }, [patternId]);

    function handleVideoComplete() {
        if (!activeVideo) {
            return;
        }

        navigate(
            `/revision/${activeVideo.id}`
        );
    }

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

            <header className="pattern-header">

                <span className="hero-eyebrow">
                    PATTERN
                </span>

                <h1>
                    {pattern.name}
                </h1>

                <p>
                    {pattern.description}
                </p>

            </header>

            {loading ? (
                <div className="loading-card">
                    Loading pattern playlist...
                </div>
            ) : (
                <div className="learning-layout">

                    <section className="lesson-area">

                        <VideoPlayer
                            video={activeVideo}
                            onComplete={
                                handleVideoComplete
                            }
                        />

                        {activeVideo && (
                            <div className="lesson-info">

                                <span>
                                    NOW LEARNING
                                </span>

                                <h2>
                                    {activeVideo.title}
                                </h2>

                                <p>
                                    {
                                        activeVideo.description ||
                                        "এই lesson-এর concept গভীরভাবে বুঝে নাও।"
                                    }
                                </p>

                            </div>
                        )}

                    </section>

                    <VideoPlaylist
                        videos={videos}
                        activeVideoId={
                            activeVideo?.id
                        }
                        onSelect={
                            setActiveVideo
                        }
                    />

                </div>
            )}

        </main>
    );
}