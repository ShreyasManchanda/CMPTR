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
    <nav className={`navbar ${scrolled ? 'navbar--scrolled' : ''} ${hidden ? 'navbar--hidden' : ''}`} aria-label="Main navigation">
      <div className="navbar__inner">
        <Link to="/" className="navbar__logo" aria-label="CMPT home">
          <span className="navbar__logo-word">CMPT</span>
          <span className="navbar__star" aria-hidden="true">*</span>
        </Link>

        <div className="navbar__links">
          {isDashboard ? (
            <>
              <NavLink label="Overview" active />
              <NavLink label="Runs" />
              <NavLink label="Competitors" />
              <NavLink label="Explain" />
            </>
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
          className="navbar__hamburger"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <span /><span /><span />
        </button>
      </div>

      {mobileOpen && (
        <div className="navbar__mobile">
          {isDashboard ? (
            <>
              <Link to="/dashboard" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>Overview</Link>
              <Link to="/dashboard" className="navbar__mobile-link" onClick={() => setMobileOpen(false)}>Runs</Link>
            </>
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

function NavLink({ label, active }) {
  return (
    <span className={`navbar__link ${active ? 'navbar__link--active' : ''}`}>{label}</span>
  );
}
