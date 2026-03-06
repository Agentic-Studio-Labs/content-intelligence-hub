import { HashRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import Dashboard from './views/Dashboard'
import Library from './views/Library'
import Generated from './views/Generated'
import ContentDetail from './views/ContentDetail'
import Settings from './views/Settings'

function App() {
  return (
    <HashRouter>
      <div className="flex h-screen">
        <nav className="w-56 border-r border-border bg-muted/30 p-4 pt-12 flex flex-col gap-1">
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
    </HashRouter>
  )
}

function SidebarLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink to={to}
      className={({ isActive }) =>
        `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
        }`
      }>
      {children}
    </NavLink>
  )
}

export default App
