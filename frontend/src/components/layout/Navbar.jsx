import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import './Navbar.css';

export default function Navbar() {
  const location = useLocation();
  const isDashboard = location.pathname === '/dashboard';
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`navbar glass ${scrolled ? 'navbar--scrolled' : ''}`}>
      <div className="navbar__inner">
        <Link to="/" className="navbar__logo">
          CMPT<span className="navbar__star">*</span>
        </Link>

        {/* Desktop nav links */}
        <div className="navbar__links">
          {isDashboard ? (
            <>
              <NavLink to="/dashboard" label="Overview" active />
              <NavLink to="/dashboard" label="Runs" />
              <NavLink to="/dashboard" label="Competitors" />
              <NavLink to="/dashboard" label="Explain" />
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
            <>
              <div className="navbar__avatar">M</div>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar__link">Log in</Link>
              <Link to="/login" className="navbar__cta">Get started</Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="navbar__hamburger"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <span /><span /><span />
        </button>
      </div>

      {/* Mobile menu */}
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
