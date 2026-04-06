// src/layouts/DashboardLayout.jsx
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export default function DashboardLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  if (!user) return null; // wait until user is loaded

  const tabs =
    user.role === "admin"
      ? [
        { key: "dashboard", label: "Dashboard", path: "/dashboard" },
        { key: "users", label: "Users", path: "/dashboard/users" },
        { key: "channels", label: "Channels", path: "/dashboard/channels" },
        { key: "download", label: "Download", path: "/dashboard/download" },
        { key: "live-streams", label: "Live Streams", path: "/dashboard/live-streams" },
        { key: "backup-download", label: "Backup Download", path: "/dashboard/backup-download" },
        { key: "backup-stream", label: "Backup Stream", path: "/dashboard/backup-stream" },
      ]
      : [
        { key: "dashboard", label: "Dashboard", path: "/dashboard" },
        { key: "download", label: "Download", path: "/dashboard/download" },
        { key: "live-streams", label: "Live Streams", path: "/dashboard/live-streams" },
      ];

  const handleLogout = () => {
    useAuthStore.getState().logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-60 bg-gray-800 text-white flex flex-col p-4">
        <h1 className="text-2xl font-bold mb-6">MVP-24/7 Monitor</h1>
        <nav className="flex flex-col space-y-2">
          {tabs.map((tab) => (
            <NavLink
              key={tab.key}
              to={tab.path}
              end={tab.path === "/dashboard"} // exact match only for dashboard
              className={({ isActive }) =>
                `text-left px-3 py-2 rounded hover:bg-gray-700 ${isActive ? "bg-gray-700 font-semibold" : ""
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={handleLogout}
          className="mt-auto bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        >
          Logout
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 bg-gray-100 p-6 overflow-auto">
        <Outlet /> {/* Dashboard child routes */}
      </div>
    </div>
  );
}