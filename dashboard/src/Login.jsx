import { useState } from 'react';

export default function LoginPage({ onLogin, loading, showToast }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await onLogin(username, password);
    } catch (error) {
      showToast('Login failed. Check your credentials.', 'error');
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>🔐 J.A.V.I.S. Login</h2>
        <p>Authenticate to access message drafts and approval workflows.</p>
        <form onSubmit={handleSubmit}>
          <label>
            Username
            <input value={username} onChange={e => setUsername(e.target.value)} placeholder="admin" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="password" />
          </label>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
