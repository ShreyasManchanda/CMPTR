import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import './Navbar.css';

export default function Navbar() {
  const location = useLocation();
  const isDashboard = location.pathname === '/dashboard';
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [hidden, setHidden] = useState(false);
  const lastY = useRef(0);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileOpen) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') setMobileOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [mobileOpen]);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      setScrolled(y > 10);

      const delta = y - (lastY.current || 0);
      if (y < 60) {
        setHidden(false);
      } else if (delta > 8) {
        setHidden(true);
      } else if (delta < -8) {
        setHidden(false);
      }
      lastY.current = y;
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      className={`navbar ${scrolled ? 'navbar--scrolled' : ''} ${hidden ? 'navbar--hidden' : ''} ${mobileOpen ? 'navbar--menu-open' : ''}`}
      aria-label="Main navigation"
    >
      <div className="navbar__inner">
        <Link to="/" className="navbar__logo" aria-label="CMPT home">
          <span className="navbar__logo-word">CMPT</span>
          <span className="navbar__star" aria-hidden="true">*</span>
        </Link>

        <div className="navbar__links">
          {isDashboard ? (
            <span className="navbar__link navbar__link--active" aria-current="page">
              Overview
            </span>
          ) : (
            <>
              <a href="#how-it-works" className="navbar__link">How it works</a>
              <a href="#features" className="navbar__link">Features</a>
              <a href="#ai-safety" className="navbar__link">AI Safety</a>
            </>
          )}
        </div>

        <div className="navbar__actions">
          {isDashboard ? (
            <div className="navbar__avatar" aria-hidden="true">M</div>
          ) : (
            <>
              <Link to="/login" className="navbar__link">Log in</Link>
              <Link to="/login" className="navbar__cta">Get started</Link>
            </>
          )}
        </div>

        <button
          type="button"
          className={`navbar__hamburger ${mobileOpen ? 'navbar__hamburger--open' : ''}`}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileOpen}
        >
          <span /><span /><span />
        </button>
      </div>

      {mobileOpen && (
        <div className="navbar__mobile" id="mobile-nav">
          {isDashboard ? (
            <Link to="/dashboard" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>
              Overview
            </Link>
          ) : (
            <>
              <a href="#how-it-works" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>How it works</a>
              <a href="#features" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>Features</a>
              <a href="#ai-safety" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>AI Safety</a>
              <Link to="/login" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>Log in</Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
