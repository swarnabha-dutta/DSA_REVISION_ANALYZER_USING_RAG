import { useEffect, useRef, useState } from "react";
import {
    getYoutubeEmbedUrl,
    extractYoutubeId,
} from "../../lib/videoUtils";
import VideoCompletion from "./VideoCompletion";

export default function VideoPlayer({
    video,
    onComplete,
}) {
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(video?.duration || 0);

    const iframeRef = useRef(null);

    const videoId =
        video?.videoId || extractYoutubeId(video?.url);

    useEffect(() => {
        if (!videoId) return;

        setCurrentTime(0);
        setDuration(video?.duration || 0);
    }, [videoId, video?.duration]);

    if (!videoId) {
        return (
            <div className="video-placeholder">
                <span>VIDEO</span>
                <p>এই ভিডিওর YouTube ID পাওয়া যায়নি।</p>
            </div>
        );
    }

    return (
        <div className="video-player-shell">
            <div className="video-player">
                <iframe
                    ref={iframeRef}
                    src={getYoutubeEmbedUrl(videoId)}
                    title={video.title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowFullScreen
                />
            </div>

            <VideoCompletion
                duration={duration}
                currentTime={currentTime}
                completed={video.completed}
                onComplete={onComplete}
            />
        </div>
    );
}