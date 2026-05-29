// J.A.V.I.S. API Client — talks to the Python FastAPI backend
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  getStats:         ()                          => request('/api/stats'),
  getConversations: (limit = 50)                => request(`/api/conversations?limit=${limit}`),
  getPending:       ()                          => request('/api/pending'),
  approve:          (msg_id, edited_draft = '') => request('/api/approve', {
    method: 'POST',
    body: JSON.stringify({ msg_id, edited_draft }),
  }),
  reject:           (msg_id)                    => request(`/api/reject/${msg_id}`, { method: 'POST' }),
  redraft:          (msg_id)                    => request(`/api/redraft/${msg_id}`, { method: 'POST' }),
  sendEmail:        (to, subject, body)         => request('/api/send/email', {
    method: 'POST',
    body: JSON.stringify({ to, subject, body }),
  }),
  sendSms:          (to, body)                  => request('/api/send/sms', {
    method: 'POST',
    body: JSON.stringify({ to, body }),
  }),
};
