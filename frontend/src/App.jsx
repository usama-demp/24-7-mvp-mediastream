// src/App.jsx
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardLayout from "./layouts/DashboardLayout";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Channels from "./pages/Channels";
import Download from "./pages/Download";
import LiveStreams from "./pages/LiveStreams";
import BackupDownload from "./pages/BackupDownload";

function App() {
  const { user } = useAuthStore(); 

  const ProtectedRoute = ({ children }) => {
    if (!user?.token) return <Navigate to="/login" replace />;
    return children;
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/dashboard/*"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          {user?.role === "admin" && <Route path="users" element={<Users />} />}
          <Route path="channels" element={<Channels />} />
          <Route path="download" element={<Download />} />
          <Route path="live-streams" element={<LiveStreams />} />
          <Route path="backup-download" element={<BackupDownload />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

export default App;