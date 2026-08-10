import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, FileSearch, History, Settings, Menu } from 'lucide-react';

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  const navItems = [
    { to: '/', icon: <LayoutDashboard size={20} />, label: 'Tableau de bord' },
    { to: '/results', icon: <FileSearch size={20} />, label: 'Résultats d\'analyse' },
    { to: '/history', icon: <History size={20} />, label: 'Historique' },
    { to: '/settings', icon: <Settings size={20} />, label: 'Paramètres' },
  ];

  return (
    <div className="app-layout">
      {/* Mobile header / toggle */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-[var(--bg-card)] border-b border-[var(--border)] z-30 flex items-center px-4" style={{ display: 'none' /* handled by media query usually, but simple approach here */ }}>
        <button onClick={toggleSidebar} className="p-2">
          <Menu size={24} />
        </button>
        <span className="font-bold text-lg ml-4">MediaCleaner</span>
      </div>

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="p-6 flex items-center gap-3 border-b border-[var(--border)]">
          <div className="w-8 h-8 rounded-lg bg-[var(--primary)] flex items-center justify-center text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 21l3-3"/><path d="M16 3l-6 6"/><path d="M21 9l-3 3"/><path d="M9 16l-3 3"/><path d="M16 11l-3 3"/><path d="M6 10l-4-4 4-4 4 4-4 4z"/></svg>
          </div>
          <h1 className="font-bold text-xl tracking-tight text-white">Media<span className="text-[var(--primary)]">Cleaner</span></h1>
        </div>
        
        <nav className="nav-list flex-1">
          {navItems.map((item) => (
            <NavLink 
              key={item.to} 
              to={item.to} 
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        
        <div className="p-4 border-t border-[var(--border)] text-xs text-muted text-center">
          v1.1.0
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
