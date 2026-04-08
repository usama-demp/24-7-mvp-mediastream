import React, { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

// Hardcoded channels with fallback URLs
const channels = [
  { name: "TRT World", channel_id: "UC7fWeaHhqgM4Ry-RMpM2YYw", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" },
  { name: "DW News", channel_id: "UCknLrEdhRCp1aegoMqRaCZg", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/test_001/stream.m3u8" },
  { name: "Al Jazeera English", channel_id: "UCNye-wNBqNL5ZzHSJj3l8Bg", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/bbb/bbb.m3u8" },
  { name: "Sky News", channel_id: "UCoMdktPbSTixAyNGwb-UYkQ", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" },
  // { name: "BBC News", channel_id: "UC16niRr50-MSBwiO3YDb3RA", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/test_001/stream.m3u8" }, 
  // { name: "CNN Live", channel_id: "UCupvZG-5ko_eiXAupbDfxWw", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/bbb/bbb.m3u8" }, 
  // { name: "INDIA TODAY", channel_id: "UCYPvAwZP8pZhSMW8qs7cVCw", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" },
  // { name: "Bol News", channel_id: "UC9Ue8P0w7X9d4h5m2K1sQ", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/test_001/stream.m3u8" },
  // { name: "NHK World Japan", channel_id: "UCSPEjw8F2nQDtmUKPFNF7_A", type: "youtube", priority: 1, fallback: "https://test-streams.mux.dev/bbb/bbb.m3u8" },
  // { name: "ARY News", channel_id: "UC4JCksJF76g_MdzPVBJoC3Q", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" }, 
  // { name: "Samaa News", channel_id: "UCJekW1Vj5fCVEGdye_mBN6Q", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/test_001/stream.m3u8" }, 
  // { name: "Hum News", channel_id: "UCRK5fC7pS1YgF0p4cJ0n7YQ", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/bbb/bbb.m3u8" }, 
  // { name: "Such News", channel_id: "UC0G9V9r1vWc0kq8E9V9KZHg", type: "youtube", priority: 3, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" },
  // { name: "Dawn News", channel_id: "UCu2J8bX4zK6p2s6vG7h5F6A", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/test_001/stream.m3u8" }, 
  // { name: "PTV News HD", channel_id: "UC9gGdVb6f2s0hP7k8YpJp3A", type: "youtube", priority: 3, fallback: "https://test-streams.mux.dev/bbb/bbb.m3u8" }, 
  // { name: "Geo News", channel_id: "UCF-NdM6m41z1H8J2P5tF0lA", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" }, 
  // { name: "Dunya News", channel_id: "UCd2vO9Yp0r2g7s8Qk3X9rHg", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/test_001/stream.m3u8" }, 
  // { name: "Express News", channel_id: "UCxkR9h2d7V0s5pJ4t9W1XgA", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/bbb/bbb.m3u8" }, 
  // { name: "GNN News", channel_id: "UC3Z0m4f7Q0l8k6N2wX5p9A", type: "youtube", priority: 2, fallback: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8" }, 
  ];

const LiveNews = () => {
  const [columns, setColumns] = useState(3); // default 3 channels per row

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif", background: "#111", minHeight: "100vh", color: "#fff" }}>
      <h2 style={{ textAlign: "center", marginBottom: "20px", fontSize: "2rem" }}>🌍 Live News Channels</h2>

      {/* Controls for user to change how many channels per row */}
      <div style={{ textAlign: "center", marginBottom: "20px" }}>
        <span>Channels per row: </span>
        {[2, 3, 4].map((num) => (
          <button
            key={num}
            onClick={() => setColumns(num)}
            style={{
              margin: "0 5px",
              padding: "5px 10px",
              cursor: "pointer",
              background: num === columns ? "#ff4500" : "#333",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              transition: "0.3s"
            }}
          >
            {num}
          </button>
        ))}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap: "20px"
        }}
      >
        {channels.map((channel, index) => (
          <ChannelCard key={index} channel={channel} />
        ))}
      </div>
    </div>
  );
};

const ChannelCard = ({ channel }) => {
  const containerRef = useRef();
  const videoRef = useRef();

  useEffect(() => {
    const playFallback = () => {
      if (!channel.fallback || !videoRef.current) return;
      const videoEl = videoRef.current;

      if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(channel.fallback);
        hls.attachMedia(videoEl);
        videoEl.style.display = "block";
        videoEl.play().catch(() => { });
      } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
        videoEl.src = channel.fallback;
        videoEl.style.display = "block";
        videoEl.play().catch(() => { });
      }
    };

    const iframe = containerRef.current?.querySelector("iframe");
    if (iframe) {
      iframe.onerror = () => {
        iframe.style.display = "none";
        playFallback();
      };
    }
  }, [channel]);

  return (
    <div
      style={{
        border: "2px solid #444",
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow: "0 0 20px rgba(255, 69, 0, 0.2)",
        transition: "transform 0.3s, box-shadow 0.3s",
        background: "#000"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "scale(1.05)";
        e.currentTarget.style.boxShadow = "0 0 30px rgba(255, 69, 0, 0.6)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "scale(1)";
        e.currentTarget.style.boxShadow = "0 0 20px rgba(255, 69, 0, 0.2)";
      }}
    >
      <h4 style={{ margin: "0", padding: "10px", background: "#222", textAlign: "center" }}>{channel.name}</h4>
      <div style={{ position: "relative", paddingTop: "56.25%" }} ref={containerRef}>
        <iframe
          style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
          src={`https://www.youtube.com/embed/live_stream?channel=${channel.channel_id}`}
          title={channel.name}
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
        <video
          ref={videoRef}
          style={{ display: "none", position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
          controls
          autoPlay
        />
      </div>
    </div>
  );
};

export default LiveNews;