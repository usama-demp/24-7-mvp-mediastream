// src/pages/Channels.jsx
import { useState, useEffect } from "react";
import toast, { Toaster } from "react-hot-toast";
import {
  fetchChannels,
  createChannel,
  updateChannel,
  deleteChannel as deleteChannelAPI,
} from "../services/api";

export default function Channels() {
  const [channels, setChannels] = useState([]);
  const [form, setForm] = useState({
    id: null,
    name: "",
    search_query: "",
    channel_live_url: "",
    allowed_terms: "",
    blocked_terms: "",
    is_enabled: true,
  });
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deleteChannel, setDeleteChannel] = useState(null);

  // Load channels
  const loadChannels = async () => {
    try {
      const data = await fetchChannels();
      setChannels(
        data.map((c) => ({
          ...c,
          allowed_terms: c.allowed_terms ? c.allowed_terms.join(", ") : "",
          blocked_terms: c.blocked_terms ? c.blocked_terms.join(", ") : "",
        }))
      );
    } catch (err) {
      toast.error(err.message);
    }
  };

  useEffect(() => {
    loadChannels();
  }, []);

  const handleChange = (e) => {
    const { name, type, checked, value } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

  const openForm = (channel = null) => {
    if (channel) setForm(channel);
    else
      setForm({
        id: null,
        name: "",
        search_query: "",
        channel_live_url: "",
        allowed_terms: "",
        blocked_terms: "",
        is_enabled: true,
      });
    setIsFormOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        allowed_terms: form.allowed_terms
          ? form.allowed_terms.split(",").map((t) => t.trim()).filter(Boolean)
          : [],
        blocked_terms: form.blocked_terms
          ? form.blocked_terms.split(",").map((t) => t.trim()).filter(Boolean)
          : [],
      };

      if (form.id) {
        await updateChannel(form.id, payload);
        toast.success("Channel updated successfully!");
      } else {
        await createChannel(payload);
        toast.success("Channel created successfully!");
      }

      setIsFormOpen(false);
      loadChannels();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleDeleteClick = (channel) => setDeleteChannel(channel);

  const confirmDelete = async () => {
    try {
      await deleteChannelAPI(deleteChannel.id);
      toast.success("Channel deleted successfully!");
      setDeleteChannel(null);
      loadChannels();
    } catch (err) {
      toast.error(err.message);
    }
  };

  return (
    <div>
      <Toaster position="top-right" />
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Channels</h1>
        <button
          onClick={() => openForm()}
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          Add Channel
        </button>
      </div>

      {/* Channels Table */}
      <div className="overflow-x-auto bg-white shadow rounded">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Enabled</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {channels.map((c) => (
              <tr key={c.id}>
                <td className="px-6 py-4">{c.name}</td>
                <td className="px-6 py-4">{c.is_enabled ? "Yes" : "No"}</td>
                <td className="px-6 py-4 space-x-2">
                  <button onClick={() => openForm(c)} className="text-blue-600 hover:underline">Edit</button>
                  <button onClick={() => handleDeleteClick(c)} className="text-red-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
            {channels.length === 0 && (
              <tr>
                <td colSpan="3" className="text-center py-4 text-gray-500">No channels found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Form */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-center z-50">
          <div className="bg-white rounded p-6 w-full max-w-md shadow-lg">
            <h2 className="text-xl font-bold mb-4">{form.id ? "Edit Channel" : "Add Channel"}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block mb-1">Channel Name</label>
                <input
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                  required
                />
              </div>

              <div>
                <label className="block mb-1">Search Query</label>
                <input
                  name="search_query"
                  value={form.search_query}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                />
              </div>

              <div>
                <label className="block mb-1">Channel Live URL</label>
                <input
                  name="channel_live_url"
                  value={form.channel_live_url}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                />
              </div>

              <div>
                <label className="block mb-1">Allowed Terms (comma separated)</label>
                <input
                  name="allowed_terms"
                  value={form.allowed_terms}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                />
              </div>

              <div>
                <label className="block mb-1">Blocked Terms (comma separated)</label>
                <input
                  name="blocked_terms"
                  value={form.blocked_terms}
                  onChange={handleChange}
                  className="w-full border px-3 py-2 rounded"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_enabled"
                  checked={form.is_enabled}
                  onChange={handleChange}
                  id="is_enabled"
                  className="h-4 w-4"
                />
                <label htmlFor="is_enabled">Enabled</label>
              </div>

              <div className="flex justify-end space-x-2">
                <button type="button" onClick={() => setIsFormOpen(false)} className="px-4 py-2 rounded border">Cancel</button>
                <button type="submit" className="px-4 py-2 rounded bg-green-500 text-white hover:bg-green-600">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteChannel && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex justify-center items-center z-50">
          <div className="bg-white rounded p-6 w-full max-w-sm shadow-lg text-center">
            <h2 className="text-xl font-bold mb-4">Confirm Delete</h2>
            <p className="mb-6">Are you sure you want to delete <strong>{deleteChannel.name}</strong>?</p>
            <div className="flex justify-center space-x-4">
              <button onClick={() => setDeleteChannel(null)} className="px-4 py-2 rounded border">Cancel</button>
              <button onClick={confirmDelete} className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}