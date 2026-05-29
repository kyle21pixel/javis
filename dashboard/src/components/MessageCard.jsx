// J.A.V.I.S. Message Card — single message display in feed
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Math.floor((Date.now() - new Date(dateStr + 'Z').getTime()) / 1000);
  if (diff < 60)   return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400)return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

export default function MessageCard({ msg, onClick, selected }) {
  const channel = msg.channel || 'email';
  const status  = msg.status  || 'pending';

  return (
    <div
      className={`message-card ${status} ${selected ? 'selected' : ''}`}
      onClick={() => onClick && onClick(msg)}
      id={`msg-card-${msg.id}`}
      style={selected ? { borderColor: 'var(--accent-blue)', background: 'var(--bg-card-hover)' } : {}}
    >
      <div className="message-card-top">
        <span className="message-sender">
          {msg.name && msg.name !== '' ? msg.name : msg.identifier || msg.sender || 'Unknown'}
        </span>
        <span className="message-time">{timeAgo(msg.created_at)}</span>
      </div>

      {msg.subject && msg.subject !== 'SMS' && (
        <div className="message-subject">📌 {msg.subject}</div>
      )}

      <div className="message-preview">
        {msg.body || msg.ai_draft || 'No content'}
      </div>

      <div className="message-badges">
        <span className={`badge badge-${channel}`}>
          {channel === 'email' ? '✉ Email' : '📱 SMS'}
        </span>
        <span className={`badge badge-${status === 'auto_sent' ? 'auto' : status}`}>
          {status === 'pending'   ? '⏳ Awaiting'  :
           status === 'sent'      ? '✅ Sent'       :
           status === 'auto_sent' ? '⚡ Auto-sent'  : status}
        </span>
      </div>
    </div>
  );
}
