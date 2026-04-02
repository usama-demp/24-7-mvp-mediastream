// src/pages/Dashboard.jsx
import { useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { fetchDashboardData } from "../services/api";

export default function Dashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboardData()
      .then((res) => setData(res))
      .catch((err) => toast.error(err.message));
  }, []);

  if (!data) return <p className="p-6">Loading dashboard...</p>;

  const role = data.role; // optional, just for stats display

  return (
    <>
      <Toaster position="top-right" />
      <div>
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded shadow">
            <h3 className="text-gray-500">Total Videos</h3>
            <p className="text-2xl font-bold">{data.total_videos}</p>
          </div>

          {role === "admin" && (
            <>
              <div className="bg-white p-6 rounded shadow">
                <h3 className="text-gray-500">Total Users</h3>
                <p className="text-2xl font-bold">{data.total_users}</p>
              </div>
              <div className="bg-white p-6 rounded shadow">
                <h3 className="text-gray-500">Total Channels</h3>
                <p className="text-2xl font-bold">{data.total_channels}</p>
              </div>
            </>
          )}
        </div>

        <p className="mt-6 text-gray-600">
          Welcome, <span className="font-semibold">{data.username}</span> ({role})
        </p>
      </div>
    </>
  );
}