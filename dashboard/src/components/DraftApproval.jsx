// J.A.V.I.S. Draft Approval Panel — review, edit, approve or reject AI drafts
import { useState } from 'react';
import { api } from '../api';

export default function DraftApproval({ msg, onDone, showToast }) {
  const [draft,    setDraft]    = useState(msg.ai_draft || '');
  const [loading,  setLoading]  = useState(false);
  const [redrafting, setRedraft] = useState(false);

  async function handleApprove() {
    setLoading(true);
    try {
      await api.approve(msg.id, draft);
      showToast('Reply sent successfully ✅', 'success');
      onDone();
    } catch (e) {
      showToast('Failed to send: ' + e.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  async function handleReject() {
    setLoading(true);
    try {
      await api.reject(msg.id);
      showToast('Message dismissed', 'info');
      onDone();
    } catch (e) {
      showToast('Error: ' + e.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  async function handleRedraft() {
    setRedraft(true);
    try {
      const res = await api.redraft(msg.id);
      setDraft(res.draft);
      showToast('AI regenerated the draft ⚡', 'info');
    } catch (e) {
      showToast('Redraft failed: ' + e.message, 'error');
    } finally {
      setRedraft(false);
    }
  }

  return (
    <div className="draft-panel" id={`draft-panel-${msg.id}`}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: 2 }}>
            {msg.channel === 'sms' ? '📱' : '✉️'}&nbsp;
            {msg.name || msg.identifier}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {msg.subject !== 'SMS' ? msg.subject : msg.identifier}
          </div>
        </div>
        <span className={`badge badge-${msg.channel}`}>
          {msg.channel === 'email' ? 'Email' : 'SMS'}
        </span>
      </div>

      {/* Original message */}
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Original Message
      </div>
      <div className="draft-original">{msg.body}</div>

      {/* AI Draft editor */}
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        AI Draft Reply — Edit before sending
      </div>
      <textarea
        className="draft-textarea"
        value={draft}
        onChange={e => setDraft(e.target.value)}
        placeholder="AI draft will appear here…"
        disabled={loading || redrafting}
      />

      {/* Actions */}
      <div className="draft-actions">
        <button className="btn btn-primary" onClick={handleApprove} disabled={loading || !draft.trim()} id={`btn-approve-${msg.id}`}>
          {loading ? '⏳ Sending…' : '✅ Approve & Send'}
        </button>
        <button className="btn btn-ghost" onClick={handleRedraft} disabled={loading || redrafting} id={`btn-redraft-${msg.id}`}>
          {redrafting ? '⚡ Regenerating…' : '⚡ Regenerate Draft'}
        </button>
        <button className="btn btn-danger" onClick={handleReject} disabled={loading} id={`btn-reject-${msg.id}`}>
          🗑 Dismiss
        </button>
      </div>
    </div>
  );
}
