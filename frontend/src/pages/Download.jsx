import { useEffect, useMemo, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import HlsCardPlayer from "../components/HlsCardPlayer";
import { fetchDownloadChannels, fetchRecordings } from "../services/api";

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = 0;

  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }

  return `${value.toFixed(value >= 100 ? 0 : value >= 10 ? 1 : 2)} ${units[i]}`;
}

function getDurationSeconds(record) {
  if (record?.recorded_from && record?.recorded_to) {
    const start = new Date(record.recorded_from).getTime();
    const end = new Date(record.recorded_to).getTime();
    const diff = Math.round((end - start) / 1000);
    if (diff > 0) return diff;
  }
  return 600;
}

export default function Download() {
  const [channels, setChannels] = useState([]);
  const [records, setRecords] = useState([]);
  const [channelId, setChannelId] = useState("");
  const [startDatetime, setStartDatetime] = useState("");
  const [endDatetime, setEndDatetime] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [activeRecordId, setActiveRecordId] = useState(null);

  const limit = 12;

  useEffect(() => {
    loadChannels();
    loadInitialRecords();
  }, []);

  const channelMap = useMemo(() => {
    const map = {};
    for (const ch of channels) {
      map[String(ch.id)] = ch.name || ch.channel_name || `Channel ${ch.id}`;
    }
    return map;
  }, [channels]);

  const getChannelName = (id) => channelMap[String(id)] || `Channel ${id}`;

  const fetchAndSetRecords = async ({
    append = false,
    nextOffset = 0,
    selectedChannelId = channelId,
    selectedStartDatetime = startDatetime,
    selectedEndDatetime = endDatetime,
  } = {}) => {
    try {
      const res = await fetchRecordings({
        channel_id: selectedChannelId || undefined,
        start_datetime: selectedStartDatetime || undefined,
        end_datetime: selectedEndDatetime || undefined,
        limit,
        offset: nextOffset,
      });

      const data = Array.isArray(res) ? res : [];

      if (append) {
        setRecords((prev) => [...prev, ...data]);
        setOffset(nextOffset + data.length);
      } else {
        setRecords(data);
        setOffset(data.length);
      }

      setHasMore(data.length === limit);
    } catch (err) {
      toast.error(err.message || "Failed to fetch recordings");
    }
  };

  const loadChannels = async () => {
    try {
      const res = await fetchDownloadChannels();
      setChannels(Array.isArray(res) ? res : []);
    } catch (err) {
      toast.error(err.message || "Failed to load channels");
    }
  };

  const loadInitialRecords = async () => {
    setLoading(true);
    await fetchAndSetRecords({
      append: false,
      nextOffset: 0,
      selectedChannelId: "",
      selectedStartDatetime: "",
      selectedEndDatetime: "",
    });
    setLoading(false);
  };

  const applyFilters = async () => {
    setActiveRecordId(null);
    setLoading(true);
    await fetchAndSetRecords({ append: false, nextOffset: 0 });
    setLoading(false);
  };

  const clearFilters = async () => {
    setChannelId("");
    setStartDatetime("");
    setEndDatetime("");
    setActiveRecordId(null);
    setLoading(true);
    await fetchAndSetRecords({
      append: false,
      nextOffset: 0,
      selectedChannelId: "",
      selectedStartDatetime: "",
      selectedEndDatetime: "",
    });
    setLoading(false);
  };

  const loadMore = async () => {
    setLoadingMore(true);
    await fetchAndSetRecords({ append: true, nextOffset: offset });
    setLoadingMore(false);
  };

  const handleDownload = (record) => {
    if (!record.download_url) {
      toast.error("No download URL found");
      return;
    }

    const a = document.createElement("a");
    a.href = record.download_url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.download = record.local_file_name || `recording_${record.id}.ts`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  return (
    <>
      <Toaster position="top-right" />

      <div className="p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">
          <div>
            <h1 className="text-2xl font-bold">Downloads</h1>
            <p className="text-sm text-gray-500">
              Play and download individual OBS recordings
            </p>
          </div>
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
                    {ch.name || ch.channel_name || `Channel ${ch.id}`}
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
                    {record.video_url ? (
                      <HlsCardPlayer
                        key={`${record.id}-${activeRecordId === record.id ? "active" : "idle"}`}
                        tsUrl={record.video_url}
                        durationSeconds={getDurationSeconds(record)}
                        autoLoad={activeRecordId === record.id}
                        isActive={activeRecordId === record.id}
                        onActivate={() => setActiveRecordId(record.id)}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                        No playable URL available
                      </div>
                    )}
                  </div>

                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="min-w-0">
                        <h2 className="font-semibold text-gray-900 line-clamp-1">
                          {getChannelName(record.channel_id)}
                        </h2>
                        <p className="text-xs text-gray-500 mt-1 break-all">
                          {record.local_file_name || `Recording ${record.id}`}
                        </p>
                      </div>

                      <span className="text-xs bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full whitespace-nowrap">
                        {getChannelName(record.channel_id)}
                      </span>
                    </div> 

                    <div className="space-y-1 mb-4 text-sm text-gray-600">
                      <p>
                        {record.created_at
                          ? new Date(record.created_at).toLocaleString()
                          : ""}
                      </p>
                      <p>Size: {formatBytes(record.file_size_bytes)}</p>
                    </div>

                    <div className="grid grid-cols-1 gap-3">
                      <button
                        type="button"
                        onClick={() => handleDownload(record)}
                        disabled={!record.download_url}
                        className={`text-center rounded-xl px-4 py-2.5 font-medium transition ${
                          record.download_url
                            ? "bg-green-600 hover:bg-green-700 text-white"
                            : "bg-gray-200 text-gray-500 cursor-not-allowed"
                        }`}
                      >
                        Download
                      </button>
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