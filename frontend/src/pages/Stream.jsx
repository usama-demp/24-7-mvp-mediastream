import { useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { fetchDownloadChannels, fetchRecordings } from "../services/api";

export default function Download() {
  const [channels, setChannels] = useState([]);
  const [records, setRecords] = useState([]);

  const [channelId, setChannelId] = useState("");
  const [startDatetime, setStartDatetime] = useState("");
  const [endDatetime, setEndDatetime] = useState("");

  const [offset, setOffset] = useState(0);
  const limit = 12;

  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadChannels();
    loadInitialRecords();
  }, []);

  const loadChannels = async () => {
    try {
      const res = await fetchDownloadChannels();
      setChannels(res || []);
    } catch (err) {
      toast.error(err.message || "Failed to load channels");
    }
  };

  const loadInitialRecords = async () => {
    try {
      setLoading(true);
      const res = await fetchRecordings({
        limit,
        offset: 0,
      });

      const data = res || [];
      setRecords(data);
      setOffset(data.length);
      setHasMore(data.length === limit);
    } catch (err) {
      toast.error(err.message || "Failed to load recordings");
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = async () => {
    try {
      setLoading(true);

      const res = await fetchRecordings({
        channel_id: channelId,
        start_datetime: startDatetime || undefined,
        end_datetime: endDatetime || undefined,
        limit,
        offset: 0,
      });

      const data = res || [];
      setRecords(data);
      setOffset(data.length);
      setHasMore(data.length === limit);
    } catch (err) {
      toast.error(err.message || "Failed to apply filters");
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = async () => {
    try {
      setChannelId("");
      setStartDatetime("");
      setEndDatetime("");
      setLoading(true);

      const res = await fetchRecordings({
        limit,
        offset: 0,
      });

      const data = res || [];
      setRecords(data);
      setOffset(data.length);
      setHasMore(data.length === limit);
    } catch (err) {
      toast.error(err.message || "Failed to reset filters");
    } finally {
      setLoading(false);
    }
  };

  const loadMore = async () => {
    try {
      setLoadingMore(true);

      const res = await fetchRecordings({
        channel_id: channelId,
        start_datetime: startDatetime || undefined,
        end_datetime: endDatetime || undefined,
        limit,
        offset,
      });

      const data = res || [];
      setRecords((prev) => [...prev, ...data]);
      setOffset((prev) => prev + data.length);
      setHasMore(data.length === limit);
    } catch (err) {
      toast.error(err.message || "Failed to load more recordings");
    } finally {
      setLoadingMore(false);
    }
  };

  const getChannelName = (id) => {
    const ch = channels.find((c) => String(c.id) === String(id));
    return ch?.name || ch?.channel_name || `Channel ${id}`;
  };

  return (
    <>
      <Toaster position="top-right" />
      <div className="p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
          <h1 className="text-2xl font-bold">Downloads</h1>
          <p className="text-sm text-gray-500">
            Browse, play, and download recorded videos
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border p-4 md:p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-2">
                Channel
              </label>
              <select
                value={channelId}
                onChange={(e) => setChannelId(e.target.value)}
                className="w-full border rounded-xl px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Channels</option>
                {channels.map((ch) => (
                  <option key={ch.id} value={ch.id}>
                    {ch.name || ch.channel_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-2">
                Start Date & Time
              </label>
              <input
                type="datetime-local"
                value={startDatetime}
                onChange={(e) => setStartDatetime(e.target.value)}
                className="w-full border rounded-xl px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-2">
                End Date & Time
              </label>
              <input
                type="datetime-local"
                value={endDatetime}
                onChange={(e) => setEndDatetime(e.target.value)}
                className="w-full border rounded-xl px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={applyFilters}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-4 py-2.5 font-medium transition"
              >
                Apply Filters
              </button>
            </div>

            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-xl px-4 py-2.5 font-medium transition"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl shadow-sm border p-8 text-center text-gray-500">
            Loading recordings...
          </div>
        ) : records.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-sm border p-8 text-center text-gray-500">
            No recordings found.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
              {records.map((record) => (
                <div
                  key={record.id}
                  className="bg-white rounded-2xl shadow-sm border overflow-hidden hover:shadow-md transition"
                >
                  <div className="bg-black aspect-video">
                    <video
                      src={record.video_url}
                      controls
                      preload="metadata"
                      className="w-full h-full"
                    />
                  </div>

                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div>
                        <h2 className="font-semibold text-gray-900 line-clamp-1">
                          {getChannelName(record.channel_id)}
                        </h2>
                        <p className="text-xs text-gray-500 mt-1">
                          ID: {record.id}
                        </p>
                      </div>

                      <span className="text-xs bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full whitespace-nowrap">
                        Channel {record.channel_id}
                      </span>
                    </div>

                    <p className="text-sm text-gray-600 mb-4">
                      {new Date(record.created_at).toLocaleString()}
                    </p>

                    <div className="grid grid-cols-2 gap-3">
                      <a
                        href={record.video_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-center bg-gray-900 hover:bg-black text-white rounded-xl px-4 py-2.5 font-medium transition"
                      >
                        Play
                      </a>

                      <a
                        href={record.video_url}
                        download
                        className="text-center bg-green-600 hover:bg-green-700 text-white rounded-xl px-4 py-2.5 font-medium transition"
                      >
                        Download
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {hasMore && (
              <div className="mt-8 flex justify-center">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-medium transition"
                >
                  {loadingMore ? "Loading..." : "Load More"}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}