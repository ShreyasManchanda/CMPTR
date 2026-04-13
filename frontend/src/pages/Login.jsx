import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import './Login.css';

export default function Login() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleLogin = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => navigate('/dashboard'), 600);
  };

  return (
    <div className="login-page">
      <Navbar />
      <div className="login-page__center">
        <div className="login-card">
          <div className="login-card__header">
            <div className="login-card__logo">CMPT<span className="login-card__star">*</span></div>
            <p className="login-card__sub">Sign in to your account</p>
          </div>
          <form onSubmit={handleLogin} className="login-card__form">
            <div className="login-card__field">
              <label htmlFor="login-email" className="login-card__label">Email</label>
              <input id="login-email" type="email" placeholder="you@company.com" required defaultValue="demo@cmpt.app" />
            </div>
            <div className="login-card__field">
              <label htmlFor="login-pass" className="login-card__label">Password</label>
              <input id="login-pass" type="password" placeholder="••••••••" required defaultValue="password123" />
            </div>
            <div className="login-card__demo-note">
              Demo mode — any credentials work
            </div>
            <button type="submit" className="login-card__submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Log in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
