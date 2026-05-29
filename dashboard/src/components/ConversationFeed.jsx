// J.A.V.I.S. Conversation Feed — unified email + SMS conversation list
import MessageCard from './MessageCard';

export default function ConversationFeed({ conversations, loading, onSelect, selected }) {
  if (loading) return <div className="spinner" />;

  if (!conversations || conversations.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📭</div>
        <h3>No conversations yet</h3>
        <p>Messages from email and SMS will appear here automatically.</p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {conversations.map(conv => (
        <MessageCard
          key={conv.id}
          msg={{
            id:         conv.id,
            identifier: conv.identifier,
            name:       conv.name,
            channel:    conv.channel,
            subject:    conv.subject,
            body:       `${conv.msg_count} message${conv.msg_count !== 1 ? 's' : ''}`,
            status:     conv.status,
            created_at: conv.updated_at,
          }}
          onClick={onSelect}
          selected={selected?.id === conv.id}
        />
      ))}
    </div>
  );
}
