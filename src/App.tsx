import { HashRouter, Routes, Route, Navigate, NavLink } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import { api } from "./api/client";
import Dashboard from "./views/Dashboard";
import Library from "./views/Library";
import Generated from "./views/Generated";
import ContentDetail from "./views/ContentDetail";
import Settings from "./views/Settings";
import Login from "./views/Login";

function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <AuthenticatedShell />
      </HashRouter>
    </AuthProvider>
  );
}

function AuthenticatedShell() {
  const { authRequired, loading, user, logout } = useAuth();
  const backend = api.backendInfo();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center text-sm text-muted-foreground">
        Loading session...
      </div>
    );
  }

  if (authRequired && !user) {
    return <Login />;
  }

  return (
    <div className="flex h-screen">
      <nav className="w-64 border-r border-border bg-muted/30 p-4 pt-10 flex flex-col gap-1">
        <div className="mb-6 px-3">
          <p className="text-sm font-semibold">Content Intelligence Hub</p>
          <p className="text-xs text-muted-foreground mt-1">
            {backend.mode === "cloud"
              ? "Cloud control plane"
              : "Local sidecar mode"}
          </p>
          {user && (
            <>
              <p className="text-xs text-muted-foreground mt-3">Signed in as</p>
              <p className="text-sm font-medium truncate">{user.email}</p>
              <button
                onClick={() => void logout()}
                className="mt-3 text-xs text-primary hover:underline"
              >
                Sign out
              </button>
            </>
          )}
        </div>
        <SidebarLink to="/dashboard">Dashboard</SidebarLink>
        <SidebarLink to="/library">Library</SidebarLink>
        <SidebarLink to="/generated">Generated</SidebarLink>
        <SidebarLink to="/settings">Settings</SidebarLink>
      </nav>
      <main className="flex-1 overflow-auto p-6">
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/library" element={<Library />} />
          <Route path="/generated" element={<Generated />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/content/:id" element={<ContentDetail />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function SidebarLink({
  to,
  children,
}: {
  to: string;
  children: React.ReactNode;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? "bg-accent text-accent-foreground"
            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

export default App;
