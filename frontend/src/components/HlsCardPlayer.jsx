import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

function buildPlaylist(tsUrl, durationSeconds = 600) {
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
}

export default function HlsCardPlayer({
  tsUrl,
  durationSeconds = 600,
  autoLoad = false,
  isActive = false,
  onActivate,
}) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const blobUrlRef = useRef(null);
  const [loaded, setLoaded] = useState(autoLoad);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoaded(autoLoad);
  }, [autoLoad]);

  useEffect(() => {
    if (!loaded || !isActive || !tsUrl || !videoRef.current) return;

    const video = videoRef.current;
    const playlistText = buildPlaylist(tsUrl, durationSeconds);
    const blob = new Blob([playlistText], {
      type: "application/vnd.apple.mpegurl",
    });
    const blobUrl = URL.createObjectURL(blob);
    blobUrlRef.current = blobUrl;

    let hls = null;

    if (Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
        maxBufferLength: 30,
        backBufferLength: 10,
      });

      hlsRef.current = hls;
      hls.loadSource(blobUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setError("");
        video.play().catch(() => {});
      });

      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data?.fatal) {
          setError(data.details || "Playback failed");
        }
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = blobUrl;
      video.play().catch(() => {});
      setError("");
    } else {
      setError("HLS not supported in this browser");
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
    };
  }, [loaded, isActive, tsUrl, durationSeconds]);

  if (!loaded || !isActive) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-black">
        <button
          type="button"
          onClick={() => {
            onActivate?.();
            setLoaded(true);
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
      {error ? (
        <div className="absolute inset-0 z-10 flex items-center justify-center text-white text-sm px-4 text-center bg-black/70">
          {error}
        </div>
      ) : null}

      <video
        ref={videoRef}
        controls
        preload="none"
        playsInline
        className="w-full h-full"
      />
    </div>
  );
}