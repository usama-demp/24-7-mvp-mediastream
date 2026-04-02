export default function InstantVideoPlayer({
  videoUrl,
  posterUrl,
  isActive,
  onActivate,
}) {
  return (
    <div className="w-full h-full bg-black">
      {!isActive ? (
        <div className="relative w-full h-full">
          {posterUrl ? (
            <img
              src={posterUrl}
              alt="Preview"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-neutral-900" />
          )}

          <div className="absolute inset-0 flex items-center justify-center bg-black/25">
            <button
              onClick={onActivate}
              className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-xl border border-white/20"
            >
              Play Video
            </button>
          </div>
        </div>
      ) : (
        <video
          src={videoUrl}
          controls
          autoPlay
          preload="metadata"
          playsInline
          className="w-full h-full"
        >
          Your browser does not support the video tag.
        </video>
      )}
    </div>
  );
}