import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';

export default function Layout({ children, gatewayId }) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/counting', label: 'Counting Nodes', icon: '🔢' },
    { path: '/inspection', label: 'Inspection Nodes', icon: '🔬' },
  ];

  return (
    <>
      {/* Mobile header */}
      <div className="mobile-header">
        <span className="mobile-header-title">OEE Gateway</span>
        <button className="hamburger" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? '✕' : '☰'}
        </button>
      </div>

      <div className="app-layout">
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <div className="sidebar-logo-icon">⚡</div>
              <div>
                <div className="sidebar-logo-text">OEE Gateway</div>
                <div className="sidebar-logo-sub">IoT Bridge Controller</div>
              </div>
            </div>
          </div>

          <nav className="sidebar-nav">
            <div className="nav-section-label">Navigation</div>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
                end={item.path === '/'}
                onClick={() => setSidebarOpen(false)}
              >
                <span className="nav-link-icon">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-footer">
            <div className="gateway-badge">
              <span className="gateway-badge-dot" />
              {gatewayId || 'GATEWAY'}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          {children}
        </main>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 99,
          }}
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  );
}
