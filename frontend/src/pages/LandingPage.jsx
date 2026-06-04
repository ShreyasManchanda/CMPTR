import { Link } from 'react-router-dom';
import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import ConfidenceBar from '../components/ui/ConfidenceBar';
import BackgroundPaths from '../components/ui/BackgroundPaths';
import {
  Link as LinkIcon, Bot, LineChart, CheckCircle2,
  MessageSquareText, ShieldCheck, Activity, AlertTriangle,
  ArrowRight, ChevronDown, Plus, Minus,
} from 'lucide-react';
import './LandingPage.css';

/* ─── Scroll reveal (IntersectionObserver) ─── */
function useReveal(opts = {}) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) el.classList.add('revealed'); },
      { threshold: opts.threshold ?? 0.12, rootMargin: opts.rootMargin ?? '0px 0px -60px 0px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return ref;
}

function Reveal({ children, className = '', delay = 0, direction = 'up' }) {
  const ref = useReveal();
  return (
    <div ref={ref} className={`reveal reveal--${direction} ${delay ? `reveal-d${delay}` : ''} ${className}`}>
      {children}
    </div>
  );
}

/* ─── Parallax wrapper — shifts content based on scroll ─── */
function useParallax(speed = 0.08) {
  const ref = useRef(null);
  const onScroll = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const offset = (rect.top - window.innerHeight / 2) * speed;
    el.style.transform = `translateY(${offset}px)`;
  }, [speed]);
  useEffect(() => {
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [onScroll]);
  return ref;
}

/* ════════════════════════════════════════════
   LANDING PAGE
   ════════════════════════════════════════════ */
export default function LandingPage() {
  const dashRef = useParallax(0.035);
  const prefersReduced = useReducedMotion();

  /* GSAP hero & preview animations (desktop only, respects reduced-motion) */
  useEffect(() => {
    const mm = window.matchMedia('(min-width: 1024px)');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!mm.matches || reduced) return; // only run on desktop and when motion is allowed

    let ctx;
    let gsapLib;
    (async () => {
      try {
        const gsapModule = await import('gsap');
        const ScrollTriggerModule = await import('gsap/ScrollTrigger');
        gsapLib = gsapModule.default || gsapModule;
        gsapLib.registerPlugin(ScrollTriggerModule.ScrollTrigger || ScrollTriggerModule.default || ScrollTriggerModule);

        const lines = document.querySelectorAll('.hero__headline-line');
        gsapLib.set(lines, { y: 36, opacity: 0 });
        gsapLib.to(lines, {
          y: 0,
          opacity: 1,
          stagger: 0.08,
          duration: 0.7,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: '.hero',
            start: 'top+=10 top',
            once: true,
          },
        });

        // Preview card subtle tilt/scale easing on scroll
        const preview = document.querySelector('.hero__preview-card');
        if (preview) {
          gsapLib.fromTo(preview,
            { rotateX: 5, rotateY: -5, scale: 1.08 },
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
            }
          );
        }
      } catch (e) {
        // fail silently — animations are progressive enhancement
        // console.warn('GSAP failed to load', e);
      }
    })();

    return () => {
      if (gsapLib && gsapLib.context) gsapLib.context(() => {});
      if (ctx && ctx.revert) ctx.revert();
    };
  }, []);

  function AnimatedHeadline({ prefersReduced }) {
    const parts = [
      { text: 'Pricing intelligence', accent: false },
      { text: 'that knows', accent: false },
      { text: 'when to act', accent: true },
      { text: '— and when not to.', accent: false },
    ];

    if (prefersReduced) {
      return (
        <h1 className="hero__headline">
          Pricing intelligence<br />that knows when to act<br />— and when not to.
        </h1>
      );
    }

    const container = {
      hidden: {},
      visible: { transition: { staggerChildren: 0.02 } },
    };

    const letter = {
      hidden: { y: 60, opacity: 0 },
      visible: { y: 0, opacity: 1, transition: { type: 'spring', stiffness: 160, damping: 22 } },
    };

    return (
      <h1 className="hero__headline">
        <motion.span variants={container} initial="hidden" animate="visible" className="hero__headline-words">
          {parts.map((part, wi) => (
            <span key={wi} className="hero__headline-word" style={{ display: 'inline-block', marginRight: '12px' }}>
              {part.text.split(' ').map((word, widx) => (
                <span key={widx} style={{ display: 'inline-block', marginRight: '10px' }}>
                  {word.split('').map((ch, i) => (
                    <motion.span key={`${wi}-${widx}-${i}`} variants={letter} className={part.accent ? 'hero__char hero__char--accent' : 'hero__char'} style={{ display: 'inline-block' }}>
                      {ch}
                    </motion.span>
                  ))}
                </span>
              ))}
              {part.accent && <em className="sr-only"> (emphasized) </em>}
            </span>
          ))}
        </motion.span>
      </h1>
    );
  }

  return (
    <div className="landing">
      <Navbar />
      <BackgroundPaths intensity={0.95} />
      <section className="hero">

        {/* existing hero content follows (kept for clarity) */}
        <div className="hero__glow" />
        <div className="hero__content">
          <div className="hero__text">
            <AnimatedHeadline prefersReduced={prefersReduced} />
            <p className="hero__sub">
              CMPT watches your competitors around the clock, analyses market signals
              in real time, and tells you exactly what to do with your pricing — backed
              by data, scored for confidence, and explained in plain language.
            </p>
            <div className="hero__ctas">
              <Link to="/login" className="hero__cta-primary">
                Analyze a product <ArrowRight size={18} />
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
                <div className="hero__preview-dots"><span /><span /><span /></div>
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

        {/* scroll indicator */}
        <div className="hero__scroll">
          <ChevronDown size={20} />
        </div>
      </section>

      {/* ── TRUST ── */}
      <section className="trust">
        <Reveal>
          <div className="trust__inner">
            <p className="trust__lead">
              Most pricing tools give you raw data dumps and leave you to figure out the rest.
            </p>
            <p className="trust__bold">
              CMPT gives you a decision — backed by real market data, scored for confidence,
              and explained in plain language.
            </p>
            <p className="trust__sub">
              No more manual competitor checks. No more pricing gut-feels. No more &quot;we
              think this is right.&quot; Just data-driven pricing intelligence, delivered in
              seconds.
            </p>
          </div>
        </Reveal>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="workflow" id="how-it-works">
        <div className="workflow__inner">
          <Reveal>
            <span className="section-eyebrow">How it works</span>
            <h2 className="section-title">Four steps. One decision.</h2>
            <p className="section-sub">
              From URL to actionable pricing recommendation, in under 30 seconds.
              No setup, no integrations, no learning curve.
            </p>
          </Reveal>
          <div className="workflow__grid">
            {[
              { n: '01', t: 'Input a product', d: 'Paste your product URL and add competitor store URLs. That\'s it — no API keys, no CSV uploads, no config files.', icon: <LinkIcon size={24} /> },
              { n: '02', t: 'Crawl & normalise', d: 'Our AI agents navigate competitor pages like a human would — reading prices, stock status, and product details through visual understanding.', icon: <Bot size={24} /> },
              { n: '03', t: 'Analyse the market', d: 'The pricing engine cross-references every data point, calculates your market position, and identifies the optimal pricing strategy.', icon: <LineChart size={24} /> },
              { n: '04', t: 'Get a recommendation', d: 'Receive a clear action (Reduce, Hold, or Review) with a confidence score and a plain-language explanation you can act on immediately.', icon: <CheckCircle2 size={24} /> },
            ].map((s, i) => (
              <Reveal key={s.n} delay={i + 1}>
                <div className="workflow__card">
                  <div className="workflow__card-icon">{s.icon}</div>
                  <span className="workflow__num">{s.n}</span>
                  <h3 className="workflow__card-title">{s.t}</h3>
                  <p className="workflow__card-desc">{s.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── DASHBOARD PREVIEW ── */}
      <section className="dash-preview" id="dashboard-preview">
        <div className="dash-preview__inner">
          <Reveal>
            <span className="section-eyebrow">Product Preview</span>
            <h2 className="section-title">Your pricing console, not another chart.</h2>
            <p className="section-sub">
              Everything your pricing team needs in one view — recommendations, competitor
              data, confidence scores, and AI-generated explanations. No noise.
            </p>
          </Reveal>
          <Reveal>
            <div className="dash-preview__frame" ref={dashRef}>
              <div className="dash-preview__glow" />
              <DashboardMock />
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section className="features" id="features">
        <div className="features__inner">
          <Reveal>
            <span className="section-eyebrow">Why CMPT</span>
            <h2 className="section-title">Built for confident decisions.</h2>
            <p className="section-sub">
              Every feature is designed around one principle: merchants should understand
              exactly why a price recommendation was made before they act on it.
            </p>
          </Reveal>
          <div className="features__grid">
            {[
              { t: 'Explainable decisions', d: 'Every recommendation comes with a multi-paragraph explanation in plain language. Not "lower your price" — but why, by how much, and what happens if you don\'t.', icon: <MessageSquareText size={24} /> },
              { t: 'Confidence-gated output', d: 'When the data is strong, you get a clear action. When it\'s ambiguous, CMPT flags it for human review instead of guessing. Low-confidence results never bypass your team.', icon: <ShieldCheck size={24} /> },
              { t: 'Competitor monitoring', d: 'Track prices, stock availability, product variations, and data freshness across any number of competitor stores. CMPT doesn\'t just scrape — it understands what it\'s looking at.', icon: <Activity size={24} /> },
              { t: 'Ambiguity handled', d: 'Mismatched SKUs? Bundled pricing? Regional variants? When data doesn\'t line up cleanly, CMPT tells you exactly what\'s unclear and what your options are.', icon: <AlertTriangle size={24} /> },
            ].map((f, i) => (
              <Reveal key={f.t} delay={(i % 2) + 1}>
                <div className="feature-card">
                  <span className="feature-card__icon">{f.icon}</span>
                  <h3 className="feature-card__title">{f.t}</h3>
                  <p className="feature-card__desc">{f.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── AI SAFETY ── */}
      <section className="ai-safety" id="ai-safety">
        <div className="ai-safety__inner">
          <Reveal>
            <span className="section-eyebrow">AI Safety</span>
            <h2 className="section-title">The engine is deterministic.<br />The AI explains.</h2>
            <p className="section-sub">
              Pricing decisions are too important to delegate to a black box.
              Here's how CMPT keeps humans in the loop at every step.
            </p>
          </Reveal>
          <div className="ai-safety__grid">
            {[
              { n: '01', t: 'Rule-based decisions', d: 'The pricing decision logic is entirely rule-based and deterministic. Given the same data, it always produces the same recommendation. AI does not make the pricing call — ever.' },
              { n: '02', t: 'AI for explanation only', d: 'AI is used to resolve ambiguous product matches and to generate the human-readable explanation. It interprets — it does not decide. The recommendation comes from math, not a language model.' },
              { n: '03', t: 'Merchant stays in control', d: 'Nothing changes automatically. Every recommendation requires your explicit action to execute. CMPT advises — you decide. That\'s the entire philosophy.' },
            ].map((c, i) => (
              <Reveal key={c.n} delay={i + 1}>
                <div className="ai-safety__card">
                  <span className="ai-safety__num">{c.n}</span>
                  <h4 className="ai-safety__card-title">{c.t}</h4>
                  <p className="ai-safety__card-desc">{c.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="faq">
        <div className="faq__inner">
          <Reveal>
            <span className="section-eyebrow">FAQ</span>
            <h2 className="section-title">Frequently asked questions</h2>
          </Reveal>
          <Reveal>
            <div className="faq__list">
              <FAQItem q="What do I need to get started?" a="Just two things: your product URL and a list of competitor store URLs. No API keys, no developer setup, no CSV exports. Paste the links, click analyze, and CMPT handles everything else." />
              <FAQItem q="Does CMPT automatically change my prices?" a="Never. CMPT provides a recommendation with full reasoning and a confidence score. You review the recommendation, understand the logic, and decide whether to act. Nothing happens without your explicit action." />
              <FAQItem q="What if the competitor data is unclear?" a="CMPT flags ambiguous results for manual review and tells you exactly what's uncertain — mismatched product variants, bundled pricing, regional differences, or stale data." />
              <FAQItem q="How is confidence calculated?" a="Confidence reflects three dimensions: product match quality, data freshness, and price stability. Scores above 70% are considered actionable." />
              <FAQItem q="Is my product data stored?" a="Analysis results are stored securely for your run history, so you can track pricing trends over time. We never share, sell, or expose merchant data to third parties." />
            </div>
          </Reveal>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section className="final-cta">
        <Reveal>
          <div className="final-cta__inner">
            <div className="final-cta__glow" />
            <h2 className="final-cta__headline">
              Ready to stop guessing<br />your prices?
            </h2>
            <p className="final-cta__sub">
              Start analyzing your competitors and making data-backed pricing decisions.
            </p>
            <Link to="/login" className="final-cta__btn">
              Start analyzing for free <ArrowRight size={18} />
            </Link>
          </div>
        </Reveal>
      </section>

      <Footer />
    </div>
  );
}

/* ═══ Sub-components ═══ */

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item ${open ? 'faq-item--open' : ''}`}>
      <button className="faq-item__q" onClick={() => setOpen(!open)}>
        <span>{q}</span>
        {open ? <Minus size={16} className="faq-item__icon" /> : <Plus size={16} className="faq-item__icon" />}
      </button>
      {open && <div className="faq-item__a">{a}</div>}
    </div>
  );
}

function DashboardMock() {
  return (
    <div className="mock-dash">
      <div className="mock-dash__chrome">
        <div className="mock-dash__dots"><span /><span /><span /></div>
        <span className="mock-dash__url">cmpt.app/dashboard</span>
      </div>
      <div className="mock-dash__header">
        <span className="mock-dash__product">Sneaker X1 Pro</span>
        <span className="mock-dash__status">● Complete</span>
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
