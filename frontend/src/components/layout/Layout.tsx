import { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import Sidebar from './Sidebar';
import { Menu, LogOut } from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuthStore();

  return (
    <div className="layout">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="layout-main">
        <header className="header">
          <button
            className="header-menu-btn"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>
          <div className="header-spacer" />
          <div className="header-user">
            <span className="header-email">{user?.email || 'User'}</span>
            <button className="btn btn-outline btn-sm" onClick={logout}>
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
