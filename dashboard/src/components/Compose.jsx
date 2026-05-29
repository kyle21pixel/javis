// J.A.V.I.S. Compose Panel — manually send email or SMS
import { useState } from 'react';
import { api } from '../api';

export default function Compose({ showToast }) {
  const [tab,     setTab]     = useState('email');
  const [to,      setTo]      = useState('');
  const [subject, setSubject] = useState('');
  const [body,    setBody]    = useState('');
  const [sending, setSending] = useState(false);

  async function handleSend(e) {
    e.preventDefault();
    if (!to.trim() || !body.trim()) return;
    setSending(true);
    try {
      if (tab === 'email') {
        await api.sendEmail(to, subject, body);
        showToast('Email sent successfully ✅', 'success');
      } else {
        await api.sendSms(to, body);
        showToast('SMS sent successfully 📱', 'success');
      }
      setTo(''); setSubject(''); setBody('');
    } catch (err) {
      showToast('Send failed: ' + err.message, 'error');
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>✏️ Compose Message</h2>
          <p>Send an email or SMS directly from J.A.V.I.S.</p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 640 }}>
        {/* Channel Tabs */}
        <div className="tabs" style={{ marginBottom: 24 }}>
          <button className={`tab ${tab === 'email' ? 'active' : ''}`} onClick={() => setTab('email')} id="compose-tab-email">
            ✉️ Email
          </button>
          <button className={`tab ${tab === 'sms' ? 'active' : ''}`} onClick={() => setTab('sms')} id="compose-tab-sms">
            📱 SMS
          </button>
        </div>

        <form onSubmit={handleSend} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 6 }}>
              {tab === 'email' ? 'To (email address)' : 'To (phone number e.g. +254...)'}
            </label>
            <input
              id="compose-to"
              type="text"
              value={to}
              onChange={e => setTo(e.target.value)}
              placeholder={tab === 'email' ? 'client@example.com' : '+254712345678'}
              required
              style={{
                width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', padding: '10px 14px', color: 'var(--text-primary)',
                fontSize: '0.875rem', outline: 'none', fontFamily: 'var(--font-main)',
              }}
            />
          </div>

          {tab === 'email' && (
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Subject
              </label>
              <input
                id="compose-subject"
                type="text"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                placeholder="Message subject…"
                style={{
                  width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)', padding: '10px 14px', color: 'var(--text-primary)',
                  fontSize: '0.875rem', outline: 'none', fontFamily: 'var(--font-main)',
                }}
              />
            </div>
          )}

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 6 }}>
              Message {tab === 'sms' && <span style={{ color: 'var(--accent-orange)' }}>({body.length}/160 chars)</span>}
            </label>
            <textarea
              id="compose-body"
              className="draft-textarea"
              value={body}
              onChange={e => setBody(e.target.value)}
              placeholder={tab === 'email' ? 'Write your email…' : 'Write your SMS (160 chars)…'}
              maxLength={tab === 'sms' ? 160 : undefined}
              required
              style={{ minHeight: tab === 'email' ? 180 : 100 }}
            />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button type="submit" className="btn btn-primary" disabled={sending} id="compose-send-btn">
              {sending ? '⏳ Sending…' : `${tab === 'email' ? '✉️ Send Email' : '📱 Send SMS'}`}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => { setTo(''); setSubject(''); setBody(''); }}>
              🗑 Clear
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
