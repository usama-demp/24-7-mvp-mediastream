import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

export default function HlsCardPlayer({
  playlistUrl,
  autoLoad = false,
  isActive = false,
  onActivate,
}) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [loaded, setLoaded] = useState(autoLoad);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoaded(autoLoad);
  }, [autoLoad]);

  useEffect(() => {
    if (!loaded || !isActive || !playlistUrl || !videoRef.current) return;

    const video = videoRef.current;
    setError("");

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 30,
        maxBufferLength: 60,
      });

      hlsRef.current = hls;
      hls.loadSource(playlistUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setError("");
        video.play().catch(() => {});
      });

      hls.on(Hls.Events.ERROR, (_, data) => {
        console.error("HLS error:", data);

        if (!data?.fatal) return;

        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          setError(data.details || "Network error while loading video.");

          try {
            hls.startLoad();
          } catch (err) {
            console.error("Failed to restart HLS load:", err);
          }
          return;
        }

        if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          setError("Media error while decoding video.");

          try {
            hls.recoverMediaError();
          } catch (err) {
            console.error("Failed to recover media error:", err);
          }
          return;
        }

        setError(data.details || "Playback failed.");
        hls.destroy();
        hlsRef.current = null;
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = playlistUrl;
      video.play().catch(() => {});
    } else {
      setError("HLS is not supported in this browser.");
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }

      if (video) {
        video.pause();
        video.removeAttribute("src");
        video.load();
      }
    };
  }, [loaded, isActive, playlistUrl]);

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
        preload="metadata"
        playsInline
        className="w-full h-full"
      />
    </div>
  );
}