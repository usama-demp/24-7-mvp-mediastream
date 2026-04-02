// src/pages/LiveStreams.jsx
import { useState, useEffect } from "react";

export default function LiveStreams() {
  const [liveChannels, setLiveChannels] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws;
    let reconnectTimer;

    const connectWebSocket = () => {
      ws = new WebSocket("ws://127.0.0.1:8000/ws/new-live-channels");

      ws.onopen = () => setConnected(true);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLiveChannels(data);
      };

      ws.onclose = () => {
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

  // return (
  //   <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-6">
      
  //     {/* HEADER */}
  //     <div className="flex justify-between items-center mb-6">
  //       <h1 className="text-3xl font-bold tracking-wide">
  //         Live Streams
  //       </h1>

  //       {/* CONNECTION STATUS */}
  //       <div className="flex items-center gap-2">
  //         <span
  //           className={`w-3 h-3 rounded-full ${
  //             connected ? "bg-green-400 animate-pulse" : "bg-red-500"
  //           }`}
  //         ></span>
  //         <span className="text-sm text-gray-300">
  //           {connected ? "Connected" : "Disconnected"}
  //         </span>
  //       </div>
  //     </div>

  //     {/* LOADING STATE */}
  //     {!connected && (
  //       <div className="flex flex-col items-center justify-center py-20">
  //         <div className="w-16 h-16 border-4 border-gray-700 border-t-blue-500 rounded-full animate-spin"></div>
  //         <p className="mt-4 text-gray-400 animate-pulse">
  //           Connecting to live streams...
  //         </p>
  //       </div>
  //     )}

  //     {/* EMPTY STATE */}
  //     {connected && liveChannels.length === 0 && (
  //       <div className="text-center py-20 text-gray-400">
  //         ⚠️ No live streams available
  //       </div>
  //     )}

  //     {/* GRID */}
  //     <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
  //       {liveChannels.map((ch) => (
  //         <div
  //           key={ch.id}
  //           className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl hover:scale-[1.02] transition-all duration-300"
  //         >
  //           {/* LIVE BADGE */}
  //           {ch.channel_live_url && (
  //             <div className="absolute top-3 right-3 flex items-center gap-2 bg-green-600 px-3 py-1 rounded-full text-xs font-semibold shadow">
  //               <span className="w-2 h-2 bg-white rounded-full animate-ping"></span>
  //               LIVE
  //             </div>
  //           )}

  //           {/* TITLE */}
  //           <div className="p-4 border-b border-white/10">
  //             <h3 className="font-semibold text-lg truncate">
  //               {ch.name}
  //             </h3>
  //           </div>

  //           {/* VIDEO / OFFLINE */}
  //           <div className="relative">
  //             {ch.channel_live_url ? (
  //               <iframe
  //                 src={
  //                   ch.channel_live_url.includes("youtube.com")
  //                     ? ch.channel_live_url.replace("watch?v=", "embed/")
  //                     : ch.channel_live_url
  //                 }
  //                 title={ch.name}
  //                 className="w-full h-56"
  //                 frameBorder="0"
  //                 allow="autoplay; encrypted-media"
  //                 allowFullScreen
  //               />
  //             ) : (
  //               <div className="flex items-center justify-center h-56 text-gray-500">
  //                 ❌ Offline
  //               </div>
  //             )}
  //           </div>

  //           {/* FOOTER */}
  //           <div className="p-3 text-xs text-gray-400 flex justify-between">
  //             <span>ID: {ch.id}</span>
  //             <span>
  //               {ch.channel_live_url ? "Streaming" : "Offline"}
  //             </span>
  //           </div>
  //         </div>
  //       ))}
  //     </div>
  //   </div>

  // );
  return (
    <div className="flex items-center justify-center h-screen bg-black text-white text-center text-2xl font-sans">
      <div>
        Coming Soon... <br />
        
      </div>
    </div>
  )
}