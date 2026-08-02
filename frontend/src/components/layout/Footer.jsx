import { Link } from 'react-router-dom';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__brand">
          <Link to="/" className="footer__logo">
            CMPT<span className="footer__star">*</span>
          </Link>
          <p className="footer__tagline">
            Pricing intelligence for e-commerce teams that want clarity over data dumps.
          </p>
        </div>

        <div className="footer__col">
          <h4 className="footer__col-title">Product</h4>
          <a href="#how-it-works" className="footer__link">How it works</a>
          <a href="#features" className="footer__link">Features</a>
          <a href="#dashboard-preview" className="footer__link">Dashboard</a>
          <a href="#ai-safety" className="footer__link">AI Safety</a>
        </div>

        <div className="footer__col">
          <h4 className="footer__col-title">Company</h4>
          <span className="footer__link footer__link--muted">Privacy (soon)</span>
          <span className="footer__link footer__link--muted">Terms (soon)</span>
          <a href="mailto:hello@cmpt.app" className="footer__link">Contact</a>
        </div>
      </div>

      <div className="footer__bottom">
        <span className="footer__copy">&copy; {new Date().getFullYear()} CMPT. All rights reserved.</span>
      </div>
    </footer>
  );
}
