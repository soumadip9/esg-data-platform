import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { api, User } from "./api";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import ReviewPage from "./pages/ReviewPage";
import UploadPage from "./pages/UploadPage";

function Layout({ user, onLogout }: { user: User; onLogout: () => void }) {
  const location = useLocation();
  const navClass = (path: string) =>
    location.pathname === path ? "nav-link active" : "nav-link";

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="logo">
          Breathe ESG
          <span>Data Review Platform</span>
        </div>
        <Link to="/" className={navClass("/")}>Dashboard</Link>
        <Link to="/review" className={navClass("/review")}>Review Queue</Link>
        <Link to="/upload" className={navClass("/upload")}>Ingestion</Link>
        <div className="user-info">
          <div>{user.first_name} {user.last_name}</div>
          <div>{user.tenant_name}</div>
          <button className="btn-secondary btn-sm" style={{ marginTop: "0.5rem" }} onClick={onLogout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/upload" element={<UploadPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.me()
      .then(setUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="login-page">
        <p>Loading…</p>
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Layout
      user={user}
      onLogout={() => {
        localStorage.removeItem("access_token");
        setUser(null);
      }}
    />
  );
}
