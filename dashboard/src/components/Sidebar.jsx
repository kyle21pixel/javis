// J.A.V.I.S. Sidebar Navigation
export default function Sidebar({ activeTab, setActiveTab, pendingCount }) {
  const navItems = [
    { id: 'dashboard', icon: '⚡', label: 'Dashboard' },
    { id: 'pending',   icon: '📬', label: 'Pending Approval', badge: pendingCount },
    { id: 'conversations', icon: '💬', label: 'Conversations' },
    { id: 'contacts',  icon: '👥', label: 'Contacts' },
    { id: 'compose',   icon: '✏️', label: 'Compose' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🤖</div>
        <div className="sidebar-logo-text">
          <h1>J.A.V.I.S.</h1>
          <span>Business Assistant</span>
        </div>
      </div>

      <span className="nav-section-label">Navigation</span>
      {navItems.map(item => (
        <button
          key={item.id}
          className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
          onClick={() => setActiveTab(item.id)}
          id={`nav-${item.id}`}
        >
          <span className="nav-icon">{item.icon}</span>
          {item.label}
          {item.badge > 0 && <span className="nav-badge">{item.badge}</span>}
        </button>
      ))}

      <div className="sidebar-footer">
        <span className="nav-section-label">System</span>
        <div className="status-indicator">
          <div className="status-dot" />
          Agent Online
        </div>
      </div>
    </aside>
  );
}
