import UniversalVideoPlayer from "../components/UniversalVideoPlayer";

export default function RollingPage() {
  const channel = "Sky News"; // dynamic channel name
  const channel_id=6;
  const rollingUrl = `http://172.16.0.55:8000/rolling/rolling.mp4?channel=${encodeURIComponent(channel)}`;

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">{channel} Rolling Stream</h1>
      <UniversalVideoPlayer src={rollingUrl} title={channel} />
    </div>
  );
}