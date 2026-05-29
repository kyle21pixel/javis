// J.A.V.I.S. — Main App Component
import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import StatsPanel from './components/StatsPanel';
import ConversationFeed from './components/ConversationFeed';
import MessageCard from './components/MessageCard';
import DraftApproval from './components/DraftApproval';
import Compose from './components/Compose';
import { api } from './api';

// ── Toast system ─────────────────────────────────────────────
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>{t.message}</div>
      ))}
    </div>
  );
}

// ── Pending Approval Page ────────────────────────────────────
function PendingPage({ pending, loading, onRefresh, showToast }) {
  const [selected, setSelected] = useState(null);

  function handleDone() {
    setSelected(null);
    onRefresh();
  }

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>📬 Pending Approval</h2>
          <p>{pending.length} message{pending.length !== 1 ? 's' : ''} awaiting your review</p>
        </div>
        <button className="btn btn-ghost" onClick={onRefresh} id="btn-refresh-pending">🔄 Refresh</button>
      </div>

      {pending.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎉</div>
          <h3>All caught up!</h3>
          <p>No messages waiting for approval right now.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1fr' : '1fr', gap: 16 }}>
          <div className="message-list">
            {pending.map(msg => (
              <MessageCard
                key={msg.id}
                msg={msg}
                onClick={setSelected}
                selected={selected?.id === msg.id}
              />
            ))}
          </div>
          {selected && (
            <DraftApproval
              key={selected.id}
              msg={selected}
              onDone={handleDone}
              showToast={showToast}
            />
          )}
        </div>
      )}
    </div>
  );
}

// ── Dashboard Page ────────────────────────────────────────────
function DashboardPage({ stats, conversations, loadingStats, loadingConv, onRefresh }) {
  return (
    <div>
      <div className="page-header">
        <div>
          <h2>⚡ Dashboard</h2>
          <p>Live overview of all your business communications</p>
        </div>
        <button className="btn btn-ghost" onClick={onRefresh} id="btn-refresh-dashboard">🔄 Refresh</button>
      </div>

      <StatsPanel stats={stats} loading={loadingStats} />

      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Conversations</span>
        </div>
        <ConversationFeed
          conversations={conversations.slice(0, 8)}
          loading={loadingConv}
          onSelect={null}
        />
      </div>
    </div>
  );
}

// ── Contacts Page ─────────────────────────────────────────────
function ContactsPage({ conversations, loading }) {
  const contacts = conversations.reduce((acc, c) => {
    if (!acc.find(x => x.identifier === c.identifier)) acc.push(c);
    return acc;
  }, []);

  if (loading) return <div className="spinner" />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>👥 Contacts</h2>
          <p>{contacts.length} unique contact{contacts.length !== 1 ? 's' : ''}</p>
        </div>
      </div>
      <div className="card">
        {contacts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">👤</div>
            <h3>No contacts yet</h3>
            <p>Contacts appear automatically when messages arrive.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                {['Name / ID', 'Channel', 'Conversations', 'Last Active'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '10px 8px', fontWeight: 600, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contacts.map((c, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 8px' }}>
                    <div style={{ fontWeight: 600 }}>{c.name || '—'}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>{c.identifier}</div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <span className={`badge badge-${c.channel}`}>{c.channel === 'email' ? '✉ Email' : '📱 SMS'}</span>
                  </td>
                  <td style={{ padding: '12px 8px', color: 'var(--text-secondary)' }}>{c.msg_count}</td>
                  <td style={{ padding: '12px 8px', color: 'var(--text-muted)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                    {c.updated_at ? new Date(c.updated_at + 'Z').toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────
export default function App() {
  const [activeTab,      setActiveTab]      = useState('dashboard');
  const [stats,          setStats]          = useState(null);
  const [conversations,  setConversations]  = useState([]);
  const [pending,        setPending]        = useState([]);
  const [loadingStats,   setLoadingStats]   = useState(true);
  const [loadingConv,    setLoadingConv]    = useState(true);
  const [loadingPending, setLoadingPending] = useState(true);
  const [toasts,         setToasts]         = useState([]);

  function showToast(message, type = 'info') {
    const id = Date.now();
    setToasts(t => [...t, { id, message, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }

  const fetchAll = useCallback(async () => {
    try {
      setLoadingStats(true);
      const s = await api.getStats();
      setStats(s);
    } catch { showToast('Could not reach J.A.V.I.S. API — is the agent running?', 'error'); }
    finally { setLoadingStats(false); }

    try {
      setLoadingConv(true);
      const c = await api.getConversations();
      setConversations(c);
    } catch {} finally { setLoadingConv(false); }

    try {
      setLoadingPending(true);
      const p = await api.getPending();
      setPending(p);
    } catch {} finally { setLoadingPending(false); }
  }, []);

  // Initial load + auto-refresh every 30s
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} pendingCount={pending.length} />

      <main className="main-content">
        {activeTab === 'dashboard' && (
          <DashboardPage
            stats={stats}
            conversations={conversations}
            loadingStats={loadingStats}
            loadingConv={loadingConv}
            onRefresh={fetchAll}
          />
        )}
        {activeTab === 'pending' && (
          <PendingPage
            pending={pending}
            loading={loadingPending}
            onRefresh={fetchAll}
            showToast={showToast}
          />
        )}
        {activeTab === 'conversations' && (
          <div>
            <div className="page-header">
              <div><h2>💬 All Conversations</h2><p>Every email and SMS thread</p></div>
              <button className="btn btn-ghost" onClick={fetchAll}>🔄 Refresh</button>
            </div>
            <div className="card">
              <ConversationFeed
                conversations={conversations}
                loading={loadingConv}
                onSelect={null}
              />
            </div>
          </div>
        )}
        {activeTab === 'contacts' && (
          <ContactsPage conversations={conversations} loading={loadingConv} />
        )}
        {activeTab === 'compose' && (
          <Compose showToast={showToast} />
        )}
      </main>

      <ToastContainer toasts={toasts} />
    </div>
  );
}
