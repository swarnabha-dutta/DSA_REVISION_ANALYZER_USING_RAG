export function extractYoutubeId(url = "") {
    if (!url) return null;

    const patterns = [
        /youtube\.com\/watch\?v=([^&]+)/,
        /youtu\.be\/([^?]+)/,
        /youtube\.com\/embed\/([^?]+)/,
        /youtube\.com\/shorts\/([^?]+)/,
    ];

    for (const pattern of patterns) {
        const match = url.match(pattern);

        if (match) {
            return match[1];
        }
    }

    return null;
}

export function getYoutubeEmbedUrl(videoId, startAt = 0) {
    if (!videoId) return "";

    const params = new URLSearchParams({
        enablejsapi: "1",
        rel: "0",
        modestbranding: "1",
        playsinline: "1",
    });

    if (startAt > 0) {
        params.set("start", String(Math.floor(startAt)));
    }

    return `https://www.youtube.com/embed/${videoId}?${params.toString()}`;
}

export function getYoutubeThumbnail(videoId) {
    if (!videoId) return "";

    return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
}

export function formatDuration(seconds = 0) {
    const value = Number(seconds);

    if (!Number.isFinite(value)) return "—";

    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const secs = Math.floor(value % 60);

    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, "0")}:${String(
            secs
        ).padStart(2, "0")}`;
    }

    return `${minutes}:${String(secs).padStart(2, "0")}`;
}