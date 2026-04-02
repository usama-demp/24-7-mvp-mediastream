import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

const API_BASE = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws/live-channels";

function HlsPlayer({ src, title }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    let hls;

    if (Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
      });
      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      video.addEventListener(
        "loadedmetadata",
        () => {
          video.play().catch(() => {});
        },
        { once: true }
      );
    }

    return () => {
      if (hls) {
        hls.destroy();
      }
    };
  }, [src]);

  return (
    <video
      ref={videoRef}
      controls
      muted
      autoPlay
      playsInline
      className="w-full h-[220px] rounded bg-black"
      title={title}
    />
  );
}

export default function LiveStreams() {
  const [liveChannels, setLiveChannels] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connectWebSocket = () => {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log("Connected to live channels WebSocket");
        setConnected(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLiveChannels(Array.isArray(data) ? data : []);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setConnected(false);
        reconnectTimer = setTimeout(connectWebSocket, 5000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Live Streams</h1>

      {!connected && (
        <div className="text-center py-8">
          <p className="text-gray-500 mb-2">Connecting to live streams...</p>
          <div className="loader border-t-4 border-blue-500 rounded-full w-12 h-12 mx-auto animate-spin"></div>
        </div>
      )}

      {connected && liveChannels.length === 0 && (
        <p className="text-gray-500">No live streams available.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {liveChannels.map((ch) => {
          const streamUrl = ch.channel_live_url
            ? `${API_BASE}${ch.channel_live_url}`
            : null;

          return (
            <div key={ch.id} className="bg-white shadow rounded p-3">
              <h3 className="font-semibold mb-2">{ch.name}</h3>

              {streamUrl ? (
                <HlsPlayer src={streamUrl} title={ch.name} />
              ) : (
                <p className="text-gray-500 text-center py-8">Offline</p>
              )}
            </div>
          );
        })}
      </div>

      <style>
        {`
          .loader {
            border-width: 4px;
            border-color: #e5e7eb;
            border-top-color: #3b82f6;
          }
        `}
      </style>
    </div>
  );
}