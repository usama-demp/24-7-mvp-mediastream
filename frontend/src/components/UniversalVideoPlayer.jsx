import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

/**
 * UniversalVideoPlayer
 * Props:
 *  - src: URL to .ts chunk (HLS) or rolling .mp4
 *  - durationSeconds: only used for ts chunk playlist
 *  - autoLoad: boolean, auto load video
 *  - title: optional title
 *  - onActivate: callback on user play
 */
export default function UniversalVideoPlayer({
  src,
  durationSeconds = 600,
  autoLoad = true,
  title = "",
  onActivate,
}) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [loaded, setLoaded] = useState(autoLoad);
  const [error, setError] = useState("");

  // Wrap .ts chunk in temporary playlist
  const buildPlaylist = (tsUrl, durationSeconds = 600) => {
    return [
      "#EXTM3U",
      "#EXT-X-VERSION:3",
      "#EXT-X-PLAYLIST-TYPE:VOD",
      `#EXT-X-TARGETDURATION:${Math.max(1, Math.round(durationSeconds))}`,
      "#EXT-X-MEDIA-SEQUENCE:0",
      `#EXTINF:${Number(durationSeconds).toFixed(3)},`,
      tsUrl,
      "#EXT-X-ENDLIST",
      "",
    ].join("\n");
  };

  useEffect(() => {
    setLoaded(autoLoad);
  }, [autoLoad]);

  useEffect(() => {
    if (!loaded || !videoRef.current || !src) return;

    const video = videoRef.current;
    let hls;
    let blobUrl;

    const isHls = src.endsWith(".m3u8") || src.endsWith(".ts");

    if (isHls) {
      // Wrap single ts file in playlist
      const playlistText = buildPlaylist(src, durationSeconds);
      const blob = new Blob([playlistText], { type: "application/vnd.apple.mpegurl" });
      blobUrl = URL.createObjectURL(blob);

      if (Hls.isSupported()) {
        hls = new Hls({ enableWorker: true, lowLatencyMode: false });
        hlsRef.current = hls;
        hls.loadSource(blobUrl);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          setError("");
          video.play().catch(() => {});
        });

        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data?.fatal) setError(data.details || "Playback failed");
        });
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = blobUrl;
        video.play().catch(() => {});
        setError("");
      } else {
        setError("HLS not supported in this browser");
      }
    } else {
      // MP4 playback (rolling)
      video.src = src;
      video.play().catch(() => {});
      setError("");

      // Auto reload near end for live streaming effect
      const interval = setInterval(() => {
        if (!video.duration) return;
        const remaining = video.duration - video.currentTime;
        if (remaining < 5) {
          video.src = src + "&t=" + Date.now(); // Force refresh
          video.load();
        }
      }, 5000);

      return () => clearInterval(interval);
    }

    return () => {
      if (hlsRef.current) hlsRef.current.destroy();
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [loaded, src, durationSeconds]);

  if (!loaded) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-black">
        <button
          type="button"
          onClick={() => {
            setLoaded(true);
            onActivate?.();
          }}
          className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-xl border border-white/20"
        >
          Play Video
        </button>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-black">
      {error && (
        <div className="absolute inset-0 z-10 flex items-center justify-center text-white text-sm px-4 text-center bg-black/70">
          {error}
        </div>
      )}

      <video
        ref={videoRef}
        controls
        preload="none"
        playsInline
        className="w-full h-full"
        title={title}
      />
    </div>
  );
}