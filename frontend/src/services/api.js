// src/services/api.js
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
console.log("API URL:", API_URL);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

async function request(method, endpoint, body = undefined, headers = {}) {
  try {
    const response = await api({
      method,
      url: endpoint,
      data: body,
      headers,
    });
    return response.data;
  } catch (err) {
    const message =
      err.response?.data?.detail ||
      err.message ||
      "Something went wrong";
    throw new Error(message);
  }
}

// Auth
export const loginUser = (credentials) => request("POST", "/login", credentials);
export const registerUser = (userData) => request("POST", "/users", userData);

// Dashboard
export const fetchDashboardData = () => request("GET", "/dashboard");

// Users CRUD
export const fetchUsers = () => request("GET", "/users");
export const createUser = (userData) => request("POST", "/users", userData);
export const updateUser = (id, userData) => request("PUT", `/users/${id}`, userData);
export const deleteUser = (id) => request("DELETE", `/users/${id}`);

// Channels CRUD
export const fetchChannels = () => request("GET", "/channels");
export const createChannel = (channelData) => request("POST", "/channels", channelData);
export const updateChannel = (id, channelData) => request("PUT", `/channels/${id}`, channelData);
export const deleteChannel = (id) => request("DELETE", `/channels/${id}`);

// Other
export const fetchLiveStreams = () => request("GET", "/settings");

// Download / recordings
export const fetchDownloadChannels = () => request("GET", "/download/channels");

export const fetchRecordings = ({
  channel_id,
  start_datetime,
  end_datetime,
  limit = 20,
  offset = 0,
} = {}) => {
  const params = new URLSearchParams();

  if (channel_id !== undefined && channel_id !== null && channel_id !== "") {
    params.append("channel_id", channel_id);
  }

  if (start_datetime) {
    params.append("start_datetime", start_datetime);
  }

  if (end_datetime) {
    params.append("end_datetime", end_datetime);
  }

  params.append("limit", String(limit));
  params.append("offset", String(offset));

  const query = params.toString();
  const endpoint = query
    ? `/download/recordings?${query}`
    : "/download/recordings";

  return request("GET", endpoint);
};

export const getRecordingPlaylistUrl = (recordId) =>
  `${API_URL}/download/recordings/${recordId}/playlist.m3u8`;

export const getRecordingDownloadUrl = (recordId) =>
  `${API_URL}/download/recordings/${recordId}/download`;

export default api;