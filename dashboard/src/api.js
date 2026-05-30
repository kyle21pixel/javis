// J.A.V.I.S. API Client — talks to the Python FastAPI backend
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
let authToken = localStorage.getItem('javis_token') || '';

export function setToken(token) {
  authToken = token || '';
  if (token) {
    localStorage.setItem('javis_token', token);
  } else {
    localStorage.removeItem('javis_token');
  }
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    headers,
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  setToken,
  login: (username, password) => request('/api/token', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }),
  getMe: () => request('/api/me'),
  getStats: () => request('/api/stats'),
  getConversations: (limit = 50) => request(`/api/conversations?limit=${limit}`),
  getPending: () => request('/api/pending'),
  approve: (msg_id, edited_draft = '') => request('/api/approve', {
    method: 'POST',
    body: JSON.stringify({ msg_id, edited_draft }),
  }),
  reject: msg_id => request(`/api/reject/${msg_id}`, { method: 'POST' }),
  redraft: msg_id => request(`/api/redraft/${msg_id}`, { method: 'POST' }),
  sendEmail: (to, subject, body) => request('/api/send/email', {
    method: 'POST',
    body: JSON.stringify({ to, subject, body }),
  }),
  sendSms: (to, body) => request('/api/send/sms', {
    method: 'POST',
    body: JSON.stringify({ to, body }),
  }),
};
