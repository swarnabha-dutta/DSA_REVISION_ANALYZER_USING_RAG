/*
 * Extract a YouTube video ID from
 * a URL or a bare YouTube ID.
 */
export function extractYoutubeId(
    value = ""
) {
    if (!value) {
        return null;
    }

    const input =
        String(value).trim();

    /*
     * Already a bare YouTube ID.
     *
     * Standard YouTube IDs are 11
     * characters long.
     */
    if (
        /^[A-Za-z0-9_-]{11}$/.test(
            input
        )
    ) {
        return input;
    }

    const patterns = [
        /youtube\.com\/watch\?v=([^&]+)/i,

        /youtu\.be\/([^?&]+)/i,

        /youtube\.com\/embed\/([^?&]+)/i,

        /youtube\.com\/shorts\/([^?&]+)/i,
    ];

    for (
        const pattern of patterns
    ) {
        const match =
            input.match(pattern);

        if (match) {
            return match[1];
        }
    }

    return null;
}

/*
 * Resolve YouTube ID from a
 * complete video object.
 */
export function resolveVideoId(
    video
) {
    if (!video) {
        return null;
    }

    return (
        video.videoId ||

        video.youtubeId ||

        extractYoutubeId(
            video.url
        ) ||

        extractYoutubeId(
            video.sourceUrl
        ) ||

        extractYoutubeId(
            video.source_url
        ) ||

        extractYoutubeId(
            video.id
        )
    );
}

/*
 * Generate a normal YouTube embed URL.
 *
 * Currently the application uses the
 * YouTube IFrame Player API directly,
 * but keeping this utility is useful
 * for future fallback / preview usage.
 */
export function getYoutubeEmbedUrl(
    videoId,
    startAt = 0
) {
    if (!videoId) {
        return "";
    }

    const params =
        new URLSearchParams({
            enablejsapi: "1",

            origin:
                window.location.origin,

            rel: "0",

            modestbranding: "1",

            playsinline: "1",
        });

    if (startAt > 0) {
        params.set(
            "start",
            String(
                Math.floor(
                    startAt
                )
            )
        );
    }

    return (
        `https://www.youtube.com/embed/${videoId}?${params.toString()}`
    );
}

/*
 * YouTube thumbnail URL.
 */
export function getYoutubeThumbnail(
    videoId
) {
    if (!videoId) {
        return "";
    }

    return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
}

/*
 * Format seconds into:
 *
 * 05:42
 *
 * or:
 *
 * 1:05:42
 */
export function formatDuration(
    seconds = 0
) {
    const value =
        Number(seconds);

    if (
        !Number.isFinite(value) ||
        value < 0
    ) {
        return "—";
    }

    const hours =
        Math.floor(
            value / 3600
        );

    const minutes =
        Math.floor(
            (value % 3600) / 60
        );

    const secs =
        Math.floor(
            value % 60
        );

    if (hours > 0) {
        return `${hours}:${String(
            minutes
        ).padStart(2, "0")}:${String(
            secs
        ).padStart(2, "0")}`;
    }

    return `${minutes}:${String(
        secs
    ).padStart(2, "0")}`;
}