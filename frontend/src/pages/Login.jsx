import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { motion } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import BackgroundPaths from '../components/ui/BackgroundPaths';
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
      <BackgroundPaths variant="login" intensity={0.5} />
      <Navbar />
      <div className="login-page__center">
        <motion.div
          className="login-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 30 }}
        >
          <div className="login-card__header">
            <div className="login-card__logo">CMPT<span className="login-card__star">*</span></div>
            <p className="login-card__sub">Sign in to your account</p>
          </div>
          <form onSubmit={handleLogin} className="login-card__form">
            <div className="login-card__field">
              <label htmlFor="login-email" className="login-card__label">Email</label>
              <input id="login-email" type="email" placeholder="demo@cmpt.app" required defaultValue="demo@cmpt.app" />
            </div>
            <div className="login-card__field">
              <label htmlFor="login-pass" className="login-card__label">Password</label>
              <input id="login-pass" type="password" placeholder="password123" required defaultValue="password123" />
            </div>
            <div className="login-card__demo-note">
              Demo mode — any credentials work
            </div>
            <motion.button
              type="submit"
              className="login-card__submit"
              disabled={loading}
              whileHover={!loading ? { scale: 1.02 } : {}}
              whileTap={!loading ? { scale: 0.98 } : {}}
            >
              {loading ? 'Signing in...' : 'Log in'}
            </motion.button>
          </form>
        </motion.div>
      </div>
    </div>
  );
}
