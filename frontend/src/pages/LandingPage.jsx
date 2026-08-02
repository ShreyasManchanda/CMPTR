import { Link } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import ConfidenceBar from '../components/ui/ConfidenceBar';
import BackgroundPaths from '../components/ui/BackgroundPaths';
import {
  Link as LinkIcon, Bot, LineChart, CheckCircle2,
  MessageSquareText, ShieldCheck, Activity, AlertTriangle,
  ArrowRight, Plus, Minus,
} from 'lucide-react';
import './LandingPage.css';

/* ─── Scroll reveal: visible by default; motion is progressive enhancement ─── */
function useReveal() {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !('IntersectionObserver' in window)) {
      el.classList.add('revealed');
      return;
    }

    el.classList.add('reveal--ready');
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('revealed');
          observer.unobserve(el);
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
    );
    observer.observe(el);

    const fallback = window.setTimeout(() => el.classList.add('revealed'), 2500);
    return () => {
      observer.disconnect();
      window.clearTimeout(fallback);
    };
  }, []);
  return ref;
}

function Reveal({ children, className = '', delay = 0 }) {
  const ref = useReveal();
  return (
    <div
      ref={ref}
      className={`reveal ${delay ? `reveal-d${delay}` : ''} ${className}`}
      style={delay ? { '--reveal-delay': `${delay * 70}ms` } : undefined}
    >
      {children}
    </div>
  );
}

function AnimatedHeadline({ prefersReduced }) {
  const lines = [
    { parts: [{ text: 'Pricing intelligence', accent: false }] },
    { parts: [{ text: 'that knows ', accent: false }, { text: 'when to act', accent: true }] },
    { parts: [{ text: '- and when not to.', accent: false }] },
  ];

  if (prefersReduced) {
    return (
      <h1 className="hero__headline">
        Pricing intelligence<br />
        that knows <em className="hero__accent">when to act</em><br />
        - and when not to.
      </h1>
    );
  }

  const lineVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: 0.08 + i * 0.1,
        duration: 0.55,
        ease: [0.16, 1, 0.3, 1],
      },
    }),
  };

  return (
    <h1 className="hero__headline">
      {lines.map((line, i) => (
        <motion.span
          key={i}
          className="hero__headline-line"
          custom={i}
          variants={lineVariants}
          initial="hidden"
          animate="visible"
        >
          {line.parts.map((part, j) => (
            <span key={j} className={part.accent ? 'hero__accent' : undefined}>
              {part.text}
            </span>
          ))}
        </motion.span>
      ))}
    </h1>
  );
}

export default function LandingPage() {
  const prefersReduced = useReducedMotion();

  useEffect(() => {
    const mm = window.matchMedia('(min-width: 1024px)');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!mm.matches || reduced) return;

    let ctx;
    (async () => {
      try {
        const gsapModule = await import('gsap');
        const ScrollTriggerModule = await import('gsap/ScrollTrigger');
        const gsapLib = gsapModule.default || gsapModule;
        const ScrollTrigger = ScrollTriggerModule.ScrollTrigger || ScrollTriggerModule.default || ScrollTriggerModule;
        gsapLib.registerPlugin(ScrollTrigger);

        ctx = gsapLib.context(() => {
          const preview = document.querySelector('.hero__preview-card');
          if (!preview) return;
          gsapLib.fromTo(
            preview,
            { rotateX: 4, rotateY: -4, scale: 1.04 },
            {
              rotateX: 0,
              rotateY: 0,
              scale: 1,
              ease: 'none',
              scrollTrigger: {
                trigger: '.hero__preview',
                start: 'top bottom',
                end: 'center center',
                scrub: 0.6,
              },
            },
          );
        });
      } catch {
        /* progressive enhancement */
      }
    })();

    return () => {
      if (ctx?.revert) ctx.revert();
    };
  }, []);

  return (
    <div className="landing">
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Navbar />
      <BackgroundPaths variant="home" />

      <main id="main-content">
        <section className="hero">
          <div className="hero__glow" />
          <div className="hero__content">
            <div className="hero__text">
              <AnimatedHeadline prefersReduced={prefersReduced} />
              <p className="hero__sub">
                Watch competitors, get a scored pricing action, and see the reasoning in plain language.
              </p>
              <div className="hero__ctas">
                <Link to="/login" className="hero__cta-primary">
                  Analyze a product <ArrowRight size={18} aria-hidden="true" />
                </Link>
                <a href="#dashboard-preview" className="hero__cta-ghost">
                  See a sample report
                </a>
              </div>
            </div>

            <div className="hero__preview">
              <div className="hero__preview-glow" />
              <div className="hero__preview-card">
                <div className="hero__preview-topbar">
                  <div className="hero__preview-dots" aria-hidden="true"><span /><span /><span /></div>
                  <span className="hero__preview-label">CMPT Live Dashboard</span>
                </div>
                <div className="hero__preview-body">
                  <div className="hero__preview-row hero__preview-row--between">
                    <span className="hero__preview-chip">yourstore.com</span>
                    <span className="hero__preview-meta">3 competitors tracked</span>
                  </div>
                  <div className="hero__preview-row">
                    <span className="hero__preview-badge">REDUCE</span>
                    <span className="hero__preview-meta">High confidence</span>
                  </div>
                  <div className="hero__preview-price">₹ 1,249</div>
                  <div className="hero__preview-meta">Currently: ₹ 1,499 · Save 16.7%</div>
                  <ConfidenceBar score={0.82} />
                  <div className="hero__preview-table">
                    <div className="hero__preview-th">
                      <span>Store</span><span>Price</span>
                    </div>
                    <div className="hero__preview-tr">
                      <span>competitor1.com</span><span className="mono">₹ 1,199</span>
                    </div>
                    <div className="hero__preview-tr">
                      <span>competitor2.com</span><span className="mono">₹ 1,299</span>
                    </div>
                  </div>
                  <p className="hero__preview-reason">
                    Your price is 16.7% above the market median. Reducing to ₹1,249 aligns
                    you competitively without triggering a race to the bottom.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="trust">
          <Reveal>
            <div className="trust__inner">
              <p className="trust__lead">
                Most pricing tools give you raw data dumps and leave you to figure out the rest.
              </p>
              <p className="trust__bold">
                CMPT gives you a decision: backed by market data, scored for confidence,
                and explained in plain language.
              </p>
              <p className="trust__sub">
                No more manual competitor checks. No more pricing gut-feels. Just
                data-driven pricing intelligence, delivered in seconds.
              </p>
            </div>
          </Reveal>
        </section>

        <section className="workflow" id="how-it-works">
          <div className="workflow__inner">
            <Reveal>
              <span className="section-eyebrow">How it works</span>
              <h2 className="section-title">Four steps. One decision.</h2>
              <p className="section-sub">
                From URL to actionable pricing recommendation in under 30 seconds.
              </p>
            </Reveal>
            <div className="workflow__grid">
              {[
                { t: 'Input a product', d: 'Paste your product URL and competitor store URLs. No API keys, CSV uploads, or config files.', icon: <LinkIcon size={24} aria-hidden="true" /> },
                { t: 'Crawl & normalise', d: 'Agents read competitor pages for prices, stock, and product details through visual understanding.', icon: <Bot size={24} aria-hidden="true" /> },
                { t: 'Analyse the market', d: 'The pricing engine cross-references every data point and finds your market position.', icon: <LineChart size={24} aria-hidden="true" /> },
                { t: 'Get a recommendation', d: 'Receive Reduce, Hold, or Review with a confidence score and plain-language explanation.', icon: <CheckCircle2 size={24} aria-hidden="true" /> },
              ].map((s, i) => (
                <Reveal key={s.t} delay={i + 1}>
                  <div className="workflow__card">
                    <div className="workflow__card-icon">{s.icon}</div>
                    <h3 className="workflow__card-title">{s.t}</h3>
                    <p className="workflow__card-desc">{s.d}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="dash-preview" id="dashboard-preview">
          <div className="dash-preview__inner">
            <Reveal>
              <h2 className="section-title">Your pricing console, not another chart.</h2>
              <p className="section-sub">
                Recommendations, competitor data, confidence scores, and explanations in one view.
              </p>
            </Reveal>
            <Reveal>
              <div className="dash-preview__frame">
                <div className="dash-preview__glow" />
                <DashboardMock />
              </div>
            </Reveal>
          </div>
        </section>

        <section className="features" id="features">
          <div className="features__inner">
            <Reveal>
              <h2 className="section-title">Built for confident decisions.</h2>
              <p className="section-sub">
                Merchants should understand why a price recommendation was made before they act.
              </p>
            </Reveal>
            <div className="features__grid features__grid--asymmetric">
              {[
                { t: 'Explainable decisions', d: 'Every recommendation includes plain-language reasoning: why, by how much, and what happens if you wait.', icon: <MessageSquareText size={24} aria-hidden="true" />, wide: true },
                { t: 'Confidence-gated output', d: 'Strong data yields a clear action. Ambiguous data is flagged for review instead of guessed.', icon: <ShieldCheck size={24} aria-hidden="true" />, wide: false },
                { t: 'Competitor monitoring', d: 'Track prices, stock, variants, and data freshness across competitor stores.', icon: <Activity size={24} aria-hidden="true" />, wide: false },
                { t: 'Ambiguity handled', d: 'Mismatched SKUs, bundles, or regional variants? CMPT tells you what is unclear and your options.', icon: <AlertTriangle size={24} aria-hidden="true" />, wide: true },
              ].map((f, i) => (
                <Reveal key={f.t} delay={(i % 2) + 1}>
                  <div className={`feature-card ${f.wide ? 'feature-card--wide' : ''}`}>
                    <span className="feature-card__icon">{f.icon}</span>
                    <h3 className="feature-card__title">{f.t}</h3>
                    <p className="feature-card__desc">{f.d}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="ai-safety" id="ai-safety">
          <div className="ai-safety__inner">
            <Reveal>
              <span className="section-eyebrow">AI Safety</span>
              <h2 className="section-title">The engine is deterministic.<br />The AI explains.</h2>
              <p className="section-sub">
                Pricing decisions are too important for a black box. Humans stay in the loop.
              </p>
            </Reveal>
            <div className="ai-safety__grid">
              {[
                { t: 'Rule-based decisions', d: 'Pricing logic is deterministic. Same data always yields the same recommendation. AI never makes the pricing call.' },
                { t: 'AI for explanation only', d: 'AI resolves ambiguous matches and writes the explanation. It interprets; math decides.' },
                { t: 'Merchant stays in control', d: 'Nothing changes automatically. Every recommendation needs your explicit action.' },
              ].map((c, i) => (
                <Reveal key={c.t} delay={i + 1}>
                  <div className="ai-safety__card">
                    <h3 className="ai-safety__card-title">{c.t}</h3>
                    <p className="ai-safety__card-desc">{c.d}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section className="faq">
          <div className="faq__inner">
            <Reveal>
              <h2 className="section-title">Frequently asked questions</h2>
            </Reveal>
            <Reveal>
              <div className="faq__list">
                <FAQItem q="What do I need to get started?" a="Your product URL and competitor store URLs. No API keys, developer setup, or CSV exports." />
                <FAQItem q="Does CMPT automatically change my prices?" a="Never. You get a recommendation with reasoning and confidence. Nothing happens without your explicit action." />
                <FAQItem q="What if the competitor data is unclear?" a="CMPT flags ambiguous results for manual review and names what is uncertain: mismatched variants, bundles, regional differences, or stale data." />
                <FAQItem q="How is confidence calculated?" a="Confidence reflects product match quality, data freshness, and price stability. Scores above 70% are considered actionable." />
                <FAQItem q="Is my product data stored?" a="Analysis results are stored for your run history so you can track trends. We never share or sell merchant data." />
              </div>
            </Reveal>
          </div>
        </section>

        <section className="final-cta">
          <Reveal>
            <div className="final-cta__inner">
              <div className="final-cta__glow" />
              <h2 className="final-cta__headline">
                Ready to stop guessing<br />your prices?
              </h2>
              <p className="final-cta__sub">
                Start analyzing competitors and make data-backed pricing decisions.
              </p>
              <Link to="/login" className="final-cta__btn">
                Start analyzing for free <ArrowRight size={18} aria-hidden="true" />
              </Link>
            </div>
          </Reveal>
        </section>
      </main>

      <Footer />
    </div>
  );
}

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  const panelId = `faq-${q.slice(0, 24).replace(/\W+/g, '-').toLowerCase()}`;

  return (
    <div className={`faq-item ${open ? 'faq-item--open' : ''}`}>
      <button
        type="button"
        className="faq-item__q"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls={panelId}
      >
        <span>{q}</span>
        {open
          ? <Minus size={16} className="faq-item__icon" aria-hidden="true" />
          : <Plus size={16} className="faq-item__icon" aria-hidden="true" />}
      </button>
      <div
        id={panelId}
        className="faq-item__panel"
        role="region"
        aria-hidden={!open}
      >
        <div className="faq-item__a">{a}</div>
      </div>
    </div>
  );
}

function DashboardMock() {
  return (
    <div className="mock-dash">
      <div className="mock-dash__chrome">
        <div className="mock-dash__dots" aria-hidden="true"><span /><span /><span /></div>
        <span className="mock-dash__url">cmpt.app/dashboard</span>
      </div>
      <div className="mock-dash__header">
        <span className="mock-dash__product">Sneaker X1 Pro</span>
        <span className="mock-dash__status">Complete</span>
      </div>
      <div className="mock-dash__body">
        <div className="mock-dash__rec">
          <span className="mock-dash__rec-badge">REDUCE</span>
          <div className="mock-dash__rec-price">₹ 1,249</div>
          <div className="mock-dash__rec-current">Currently: ₹ 1,499</div>
          <div className="mock-dash__rec-bar"><div className="mock-dash__rec-fill" /></div>
          <div className="mock-dash__rec-conf">82% confidence · 3 sources</div>
        </div>
        <div className="mock-dash__stats">
          <div className="mock-dash__stat"><div className="mock-dash__stat-val">₹1,199</div><div className="mock-dash__stat-lbl">Min price</div></div>
          <div className="mock-dash__stat"><div className="mock-dash__stat-val">₹1,282</div><div className="mock-dash__stat-lbl">Median</div></div>
          <div className="mock-dash__stat"><div className="mock-dash__stat-val">3</div><div className="mock-dash__stat-lbl">Competitors</div></div>
          <div className="mock-dash__stat"><div className="mock-dash__stat-val">0.83</div><div className="mock-dash__stat-lbl">Avg confidence</div></div>
        </div>
      </div>
    </div>
  );
}
