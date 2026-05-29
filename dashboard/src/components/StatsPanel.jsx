// J.A.V.I.S. Stats Panel — live metrics grid
export default function StatsPanel({ stats, loading }) {
  const cards = [
    { label: 'Total Messages',      value: stats?.total_messages    ?? '—', icon: '📨' },
    { label: 'Pending Approval',    value: stats?.pending_approval  ?? '—', icon: '⏳' },
    { label: 'Sent Today',          value: stats?.sent_today        ?? '—', icon: '✅' },
    { label: 'Open Conversations',  value: stats?.open_conversations ?? '—', icon: '💬' },
    { label: 'Total Contacts',      value: stats?.total_contacts    ?? '—', icon: '👥' },
  ];

  return (
    <div className="stats-grid">
      {cards.map(card => (
        <div className="stat-card" key={card.label}>
          <span className="stat-icon">{card.icon}</span>
          <div className="stat-label">{card.label}</div>
          <div className="stat-value">
            {loading ? <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>…</span> : card.value}
          </div>
        </div>
      ))}
    </div>
  );
}
