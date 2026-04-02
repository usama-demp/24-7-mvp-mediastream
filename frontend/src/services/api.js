// src/services/api.js

const API_URL = "http://172.16.1.7:8000"; // your backend URL

// Generic request function
async function request(endpoint, { method = "GET", body, headers = {} } = {}) {
  const token = localStorage.getItem("token");

  const res = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Something went wrong");
  }

  return data;
}

// Auth
export const loginUser = (credentials) => request("/login", { method: "POST", body: credentials });
export const registerUser = (userData) => request("/users", { method: "POST", body: userData });

// Dashboard
export const fetchDashboardData = () => request("/dashboard");

// Users CRUD
export const fetchUsers = () => request("/users");
export const createUser = (userData) => request("/users", { method: "POST", body: userData });
export const updateUser = (id, userData) => request(`/users/${id}`, { method: "PUT", body: userData });
export const deleteUser = (id) => request(`/users/${id}`, { method: "DELETE" });

// Channels CRUD
export const fetchChannels = () => request("/channels");
export const createChannel = (channelData) => request("/channels", { method: "POST", body: channelData });
export const updateChannel = (id, channelData) => request(`/channels/${id}`, { method: "PUT", body: channelData });
export const deleteChannel = (id) => request(`/channels/${id}`, { method: "DELETE" });


//
export const fetchLiveStreams = () => request("/settings");


export const fetchDownloadChannels = () => request("/download/channels");

export const fetchRecordings = ({
  channel_id,
  start_datetime,
  end_datetime,
  limit = 20,
  offset = 0,
}) => {
  const params = new URLSearchParams();

  if (channel_id !== undefined && channel_id !== "") {
    params.append("channel_id", channel_id);
  }

  if (start_datetime) {
    params.append("start_datetime", start_datetime);
  }

  if (end_datetime) {
    params.append("end_datetime", end_datetime);
  }

  params.append("limit", limit);
  params.append("offset", offset);

  return request(`/download/recordings?${params.toString()}`);
};