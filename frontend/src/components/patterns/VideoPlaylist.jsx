export default function VideoPlaylist({
    videos = [],
    activeVideoId,
    onSelect,
}) {
    return (
        <aside className="video-playlist">
            <div className="playlist-header">
                <div>
                    <span className="ai-panel-label">PLAYLIST</span>
                    <h3>Pattern Lessons</h3>
                </div>

                <span>{videos.length} videos</span>
            </div>

            <div className="playlist-items">
                {videos.map((video, index) => {
                    const active = video.id === activeVideoId;

                    return (
                        <button
                            key={video.id}
                            className={`playlist-item ${active ? "playlist-item-active" : ""
                                }`}
                            onClick={() => onSelect(video)}
                        >
                            <span className="playlist-index">
                                {String(index + 1).padStart(2, "0")}
                            </span>

                            <span className="playlist-info">
                                <strong>{video.title}</strong>

                                <small>
                                    {video.durationText || "Video"}
                                </small>
                            </span>

                            {video.completed && (
                                <span className="playlist-check">✓</span>
                            )}
                        </button>
                    );
                })}
            </div>
        </aside>
    );
}