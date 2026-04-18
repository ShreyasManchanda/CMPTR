# CMPT Frontend PRD
**Version:** 3.0 (Full Modernization — Prioritized, Resolved, Production-Ready)
**Scope:** Landing Page + Dashboard + Micro-interactions & Scroll Animations
**Backend:** Fully built (FastAPI). Frontend wires to real API.
**Auth:** Mock auth only (no real backend auth exists yet — see Section 12 for migration path)

---

## 1. Product Identity & Vision

CMPT is a premium pricing intelligence console. It is not a generic scraper; it is a high-end, decision-making engine. A merchant provides a product URL and competitor URLs. CMPT crawls, normalizes, analyzes, and returns a recommended pricing action with a confidence score and a human-readable explanation.

The UI must feel like a cutting-edge, high-performance tool — akin to modern developer tools and high-end SaaS platforms (e.g., Linear, Vercel, Raycast). It must communicate speed, precision, and control.

**Three things the UI must make immediately clear:**

1. This tool watches competitors with precision.
2. It recommends what to do — with a data-backed reason.
3. The merchant stays in control. Nothing changes automatically.

**Logo note:** The CMPT logo includes a `*` (asterisk) as part of its visual identity. This is intentional and must be preserved in all UI implementations.

**DESIGN.md protocol:** A `DESIGN.md` file must be placed in the project root before any component is written. It acts as the single source of truth for color tokens, typography roles, and spacing. All AI coding agents and developers must read this file before generating or editing UI code. The DESIGN.md is generated from the design system defined in Section 2 of this document.

---

## 2. Design System

### 2.1 Color Palette

Use CSS custom properties throughout. The base is near-black (not pure black — pure black causes visual fatigue and excessive contrast during long sessions).

| Token | Value | Usage |
|---|---|---|
| `--bg-base` | `#050505` | Deepest background |
| `--bg-surface-1` | `#0A0A0A` | Primary card backgrounds |
| `--bg-surface-2` | `#121212` | Nested surfaces, table rows, hover states |
| `--border` | `rgba(255,255,255,0.06)` | Subtle dividers and card borders |
| `--border-glow` | `rgba(52,211,153,0.15)` | Accent borders for active/focused states |
| `--text-primary` | `#FAFAFA` | Headlines, primary labels |
| `--text-secondary` | `#A1A1AA` | Subtext, metadata, muted text |
| `--accent` | `#10B981` | Electric Emerald — CTAs, badges, highlights |
| `--accent-glow` | `rgba(16,185,129,0.25)` | Soft glow behind accent elements |
| `--error` | `#EF4444` | Error states |
| `--warning` | `#F59E0B` | Ambiguity / manual review states |
| `--glass-bg` | `rgba(10,10,10,0.6)` | Glass surfaces (Navbar, Modals) |
| `--glass-border` | `rgba(255,255,255,0.08)` | Glass borders |

### 2.2 Typography

Strictly avoid pure white (`#FFFFFF`). Use `#FAFAFA` to preserve luminance intent without eye strain in dark mode.

| Role | Font | Weight | Size |
|---|---|---|---|
| Hero headline | `'Playfair Display', serif` | 700 | 72–96px, tight tracking |
| Hero italic accent | `'Playfair Display', serif` | 400 italic | Same as above |
| Section headers | `'Inter', sans-serif` | 500 | 24–32px, slightly tight tracking |
| Body / labels | `'Inter', sans-serif` | 400 | 14–16px |
| Monospace data | `'Geist Mono', monospace` | 400 | 13px |
| Numbers / metrics | `'Inter', sans-serif` | 500 | Context dependent |

### 2.3 Elevation & Depth

Drop shadows are imperceptible on `--bg-base`. Depth is expressed through surface lightness: higher elevation = lighter surface color. Cards use `--bg-surface-1` and shift to `--bg-surface-2` on hover to simulate moving closer to the user. Glassmorphism (`backdrop-filter: blur(16px) saturate(180%)`) is used sparingly — navbar and modals only.

### 2.4 Border Radius & Shadows

- Cards: `16px`
- Buttons: `8px` (standard) or `99px` (pill — primary CTAs only)
- Badges / chips: `999px`
- Input fields: `12px`

```css
--shadow-card: inset 0 1px 0 rgba(255,255,255,0.05);
--shadow-glow: 0 0 32px -8px var(--accent-glow);
```

### 2.5 Gradient & Glow

```css
/* Primary button */
background: linear-gradient(135deg, #10B981 0%, #059669 100%);
box-shadow: 0 0 24px -6px rgba(16,185,129,0.4), inset 0 1px 0 rgba(255,255,255,0.2);
```

---

## 3. Motion Language & Animation Stack

### 3.1 Principles

- **Snappy & physical:** Use spring physics, not linear easing.
- **Staggered reveals:** Lists and grids reveal items sequentially.
- **No scroll-jacking:** Scroll-driven animations must progress in direct 1:1 relation to the user's native scroll velocity. Never hijack trackpad or mouse wheel.
- **Respect `prefers-reduced-motion`:** All animations (particles, parallax, Border Beam, typewriter) must instantly default to static states when this OS setting is enabled. This is not optional.

### 3.2 Library Responsibilities

| Library | Responsibility | Route |
|---|---|---|
| Framer Motion | Micro-interactions, spring physics, layout animations, hover states | `/dashboard` primarily |
| GSAP + ScrollTrigger | Scroll-driven sequences, pinned sections | `/` landing page only |
| GSAP SplitText | Text reveal animations | `/` landing page hero only |

> **Rule:** GSAP scroll sequences run only on desktop viewports. Use `gsap.matchMedia()` to wrap all setup code so sequences revert cleanly on mobile, preventing layout breaks and lag.

### 3.3 Micro-Interactions (Framer Motion) — Dashboard

| Element | Interaction | Spec |
|---|---|---|
| Primary button | Hover | `scale: 1.05`, glow intensity increases |
| Primary button | Tap | `scale: 0.95` |
| Cards | Hover | `y: -4`, background shifts to `--bg-surface-2` |
| Dashboard load | Mount | Staggered fade-up (`y: 20, opacity: 0→1`), `staggerChildren: 0.05` |
| Number counters | Data load | Animate from 0 to value over 0.8s, ease-out |
| Tabs / filters | Active state | Animated layout background pill (`layoutId`) |

### 3.4 Scroll Animations (GSAP) — Landing Page Only

| Section | Effect |
|---|---|
| Hero headline | Line-by-line reveal via `SplitText`. Italic phrase glows on load. |
| Hero dashboard preview | Scroll-linked: `rotateX: 5→0`, `rotateY: -5→0`, `scale: 1.1→1.0`. No velocity hijacking. |
| Workflow steps | CSS `position: sticky` pinning. Steps slide in horizontally at native scroll pace. |
| Feature bento grid | Fade and slide-up (`y: 50, rotation: 2, opacity: 0→1`) triggered at 20% viewport entry. |
| AI Safety section | Sequential staggered fade-up on scroll. |

---

## 4. Component Library

| Component | Notes |
|---|---|
| `Navbar` | Glassy, sticky. Hides on scroll down, reveals on scroll up. |
| `HeroSection` | Serif headline with GSAP text reveal. Particle background (desktop, non-reduced-motion only). |
| `BentoGrid` | Asymmetric grid. Hover glows track cursor via `--mouse-x / --mouse-y`. |
| `StatCard` | Single metric. Number animates on load. Shimmer skeleton before data resolves. |
| `RecommendationCard` | Primary dashboard card. Pulsing glow when action is required. |
| `ConfidenceRing` | Circular SVG progress ring. Replaces flat progress bar. |
| `CompetitorRow` | Table row. Hover reveals "View Source" link. |
| `TrendChart` | Minimalist area chart (Recharts). Gradient fill, animated line on load. **Lazy-loaded.** |
| `ExplanationPanel` | Markdown-rendered AI explanation. Typewriter effect on initial load. |
| `AnimatedButton` | Gradient button with shine effect on hover. Idle: subtle pulsing glow. |
| `SuggestionPanel` | Competitor discovery results. Checkbox list with store name, URL, match hint. |
| `SkeletonScreen` | Structural skeleton for all dashboard cards and tables during API calls. |

---

## 5. Page Structure

```
/          → Landing page (marketing, scroll animations)
/dashboard → App dashboard (app-like, Framer Motion micro-interactions)
/login     → Mock login page (minimalist, centered)
```

---

## 6. Landing Page (`/`)

### 6.1 Navbar

- Glassy, sticky, height: 64px.
- Left: `CMPT *` wordmark in Inter Bold, electric emerald dot on the asterisk.
- Center: Nav links with animated underline on hover.
- Right: `Log in` (ghost button), `Get started` (pill-shaped, emerald, subtle glow).

### 6.2 Hero Section

**Background:** Interactive particle canvas — 100 muted emerald nodes, connecting lines drawn between nearby particles, cursor attraction on mouse move. Built with HTML5 Canvas API and `requestAnimationFrame`.

**Performance gate (critical):** The particle canvas renders only when all three conditions are met: (1) desktop viewport, (2) `prefers-reduced-motion: no-preference`, (3) device is not flagged as low-power. On failure of any condition, fall back to a static radial gradient (`radial-gradient(ellipse at 50% 0%, rgba(16,185,129,0.08) 0%, transparent 70%)`).

**Headline (Playfair Display, serif):**
> Pricing intelligence that knows  
> *when to act* — and when not to.

Animation: GSAP `SplitText` line-by-line reveal. Italic phrase has subtle emerald `text-shadow` on load.

**Subheadline (Inter):**
> CMPT watches your competitors, analyses the market, and tells you exactly what to do with your pricing — and why.

**CTAs:**
- Primary: `Analyze a product` — gradient button with Magic UI Border Beam (`color: #10B981`, `duration: 6s`). Border Beam only renders on desktop and when `prefers-reduced-motion: no-preference`.
- Secondary: `See a sample report` — outlined button with animated border glow on hover.

**Hero Dashboard Preview:**
- Initial state: `rotateX: 5deg`, `rotateY: -5deg`, `scale: 1.1`.
- On scroll: GSAP ScrollTrigger transitions to `rotateX: 0`, `rotateY: 0`, `scale: 1.0`.
- Native scroll pace is strictly preserved.

### 6.3 Problem Statement

Large centered typography, fade-up on scroll:

> Most pricing tools give you raw data and leave you to figure out the rest.  
> **CMPT gives you a decision.**

### 6.4 Workflow (Pinned Scroll Section)

GSAP pinned section. Left column stays pinned with "How it works". Right column scrolls through the four steps, with an animated accent bar highlighting the active step.

Steps:
1. Input a product
2. Crawl & normalise
3. Analyse the market
4. Get a recommendation

Scroll must advance at the user's native pace. Do not artificially slow or fast the progression.

### 6.5 Feature Highlights (Bento Grid)

Asymmetric bento grid layout. Cards:

- **Explainable decisions** (large card) — shows the AI explanation UI
- **Confidence-gated output** (small card) — shows the confidence ring
- **Competitor monitoring** (wide card) — shows a snippet of the competitor table
- **Ambiguity handled** (small card) — shows the warning state

Hover: radial gradient glow beneath each card border tracks cursor position via CSS `--mouse-x / --mouse-y`.

### 6.6 AI Safety Section

Muted section with subtle gradient background. Headline: "The engine is deterministic. The AI explains." Three minimalist columns, staggered fade-up on scroll.

### 6.7 Footer

Minimal. Logo left. Links center. `© 2026 CMPT` right.

---

## 7. Mock Login Page (`/login`)

- Deep background with subtle radial gradient.
- Centered glassmorphic card, glowing border on input focus.
- `CMPT *` wordmark glowing subtly at top.
- Inputs: emerald border + glow on focus.
- `Log in` button: loading spinner state on click, then redirect to `/dashboard`.

---

## 8. Dashboard Page (`/dashboard`)

The dashboard must feel like a native app. Zero page reloads. Instant feedback. **No particle effects, no heavy GSAP scroll sequences.** The dashboard prioritizes clarity, speed, and daily usability over cinematic effect.

### 8.1 Layout

```
┌─────────────────────────────────────────────┐
│  TOP ZONE: Header bar                        │
│  Product name | Run status | Run button      │
├──────────────────────────┬──────────────────┤
│  MAIN ZONE               │  SIDE ZONE       │
│  Recommendation card     │  Market stats    │
│  Explanation panel       │  Confidence ring │
│  Ambiguity panel (cond.) │                  │
├──────────────────────────┴──────────────────┤
│  LOWER ZONE                                  │
│  Competitor list (sleek table)               │
│  Trend chart (lazy-loaded)                   │
└─────────────────────────────────────────────┘
```

### 8.2 Top Zone

- Left: Product name.
- Center: `RunStatusBadge` — pulses when analysis is running.
- Right: `Run Analysis` button with gradient glow. Sweeping shine animation on hover.

### 8.3 Empty State — Input Form

Centered card layout.

**Inputs:**
- My product URL (text input with focus glow)
- Competitor store URLs (tag-style textarea — pressing Enter creates a chip)

**Auto Discover Competitors:**

Below the competitor URLs field, add a `Find competitors` button.

**Behavior:**
- Disabled unless a valid product URL is present (validated client-side before enabling).
- On click: POST to `/api/v1/competitors/discover` with `{ product_url: string }`.
- Request payload: `{ product_url: string }`
- Response payload: `{ suggestions: Array<{ name: string, url: string, match_hint: string }> }` where `match_hint` is one of: `"Similar category"`, `"Price range match"`, `"Same brand segment"`, or `null`.
- The button shows an inline spinner and the label "Finding competitors…" during the request.

**Suggestion Panel (on success):**
- Title: `Suggested competitors` with a small badge: `AI suggested`.
- Checkbox list — all checked by default.
- Each row: store name, URL, and `match_hint` badge if present.
- CTA: `Add selected to list` — appends checked items to the competitor URL field as chips.

**States:**

| State | UI |
|---|---|
| Idle | Panel hidden |
| Loading | Spinner, "Finding competitors…" label |
| Success | Panel visible with suggestions |
| No results | "No competitor stores found. Try a different product URL." |
| Error | Inline error message below the button. Form remains usable. |

### 8.4 Run Analysis Button

Gradient glow button with sweeping shine animation on hover. On click: transitions to results view and triggers analysis API call.

### 8.5 Results View & UX States

**Skeleton loading strategy:** When an analysis is running, render the full structural skeleton of all cards, tables, and chart areas immediately. Use a left-to-right shimmer (`--bg-surface-2` to `--bg-surface-1`, 1.5s loop) to indicate active processing. Never show a blank screen or a single centered spinner.

**Error & empty states:** Never show raw API error text. If competitor data is blocked or unavailable, show a friendly empty-state with a human-readable explanation and an explicit next step (e.g., "We couldn't scrape this competitor. Please verify the URL or try a different store.").

### 8.6 Recommendation Card

- Large, prominent card with left border accent in `--accent`.
- Headline: recommended action — `REDUCE`, `MAINTAIN`, or `INCREASE`.
- Animated `ConfidenceRing` (circular SVG, not a flat bar).
- Plain-language explanation of the recommendation.
- Pulsing glow on the card border when action type is `REDUCE` or `INCREASE`.

### 8.7 Explanation Panel

- Markdown-rendered.
- Typewriter effect reveals text on initial load (character-by-character, ~30ms interval).
- No typewriter on re-renders or cached results — only on first mount.

### 8.8 Competitor List

- Sleek table. Row background shifts to `--bg-surface-2` on hover.
- Prices lower than the merchant's: highlighted in `--error` (`#EF4444`).
- Prices higher than the merchant's: highlighted in emerald (`--accent`).
- Hover reveals a "View Source" link inline on each row.

### 8.9 Trend Chart

- Minimalist area chart (Recharts). No grid lines — data line and gradient fill only.
- Gradient fill fades to transparent at the bottom.
- Smooth tooltip follows mouse.
- **Lazy-loaded via `React.lazy` + `Suspense`** to preserve initial dashboard render performance.

---

## 9. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Next.js (App Router) or Vite + React | SSR for landing page SEO; instant client nav for dashboard |
| Styling | Tailwind CSS with CSS custom properties | Token-based theming; DESIGN.md maps directly to config |
| UI components | Magic UI, Aceternity UI (selective) | Border Beam, particle canvas — not wholesale adoption |
| Micro-interactions | Framer Motion | Spring physics, `layoutId`, `AnimatePresence` |
| Scroll animations | GSAP + ScrollTrigger + SplitText | Landing page only |
| Charts | Recharts | Minimal setup, sufficient for trend chart |
| Icons | Lucide React | Consistent, tree-shakeable |

---

## 10. MVP Scope vs. V2 (Priority Tiers)

### Tier 1 — MVP (ship this first)

- [ ] `/login` mock page
- [ ] `/dashboard` empty state with input form
- [ ] Run Analysis flow with skeleton loading
- [ ] Recommendation card + Confidence ring
- [ ] Explanation panel (typewriter)
- [ ] Competitor table
- [ ] Error and empty states
- [ ] `prefers-reduced-motion` support throughout

### Tier 2 — V1.1 (after core flow is stable)

- [ ] Auto Discover Competitors feature
- [ ] Trend chart (lazy-loaded)
- [ ] `/` landing page — static version (no scroll animations yet)
- [ ] Navbar (glassy, scroll-hide behavior)

### Tier 3 — V2 (polish and marketing)

- [ ] GSAP scroll animations on landing page (SplitText, pinned workflow, bento grid)
- [ ] Particle canvas hero background (with all performance gates)
- [ ] Magic UI Border Beam on hero CTA
- [ ] Hero dashboard preview parallax tilt
- [ ] Bento grid cursor-tracking hover glows

---

## 11. Performance & Accessibility Requirements

These are non-negotiable and apply to every tier.

**`prefers-reduced-motion`:** All animations — Border Beam, particle canvas, parallax, typewriter — must default to static states when the user's OS motion preference is set to reduce. Check with both CSS `@media (prefers-reduced-motion: reduce)` and JS `matchMedia`.

**No scroll-jacking:** Scroll-driven animations must progress at the user's native scroll speed in strict 1:1 relation. No artificial easing applied to scroll velocity.

**Canvas performance:** The particle canvas must use `requestAnimationFrame`. On detection of a low-power device or `prefers-reduced-motion: reduce`, disable the canvas and fall back to a static radial gradient. Detection heuristics: `navigator.hardwareConcurrency <= 4`, `navigator.deviceMemory <= 2`, or `connection.saveData === true`.

**GSAP mobile gating:** All GSAP scroll sequences must be wrapped in `gsap.matchMedia()`. On mobile viewports, sequences must not run, and must revert cleanly without leaving orphaned inline styles.

**Dashboard animation budget:** The dashboard may use Framer Motion spring animations (cards, counters, stagger reveals) and the typewriter effect. No particle canvas, no GSAP timelines, no Border Beam. The goal is fast, focused daily use.

**Concurrent animation limit:** At any given moment, no more than one intensive effect should be active in a single viewport. On the landing page, the particle canvas and GSAP timeline are sequenced — the canvas runs in the hero, GSAP timelines activate on scroll past the hero.

**WCAG AA contrast:** All text must maintain a minimum 4.5:1 contrast ratio against its background, including when `--accent-glow` overlays are active.

**Lazy loading:** `TrendChart` must be wrapped in `React.lazy` + `Suspense`. Do not import it at the top level of the dashboard.

---

## 12. Mock Auth — Migration Path

The current auth is mock-only (hardcoded credentials, no backend validation). When real auth is implemented:

- Replace the mock login handler with a call to the auth endpoint (JWT or session-based TBD).
- The `/dashboard` route must be protected with a route guard — redirect unauthenticated users to `/login`.
- Do not bake mock credential logic into shared utilities. Keep it isolated in `lib/auth/mock.ts` so it can be deleted cleanly.
- The login form's shape (email + password fields, loading state, redirect on success) should not need to change when real auth lands.

---

## 13. Must-Have Checklist

- [ ] Deep black base (`#050505`), off-white text (`#FAFAFA`) — not pure white
- [ ] Single accent color: Electric Emerald `#10B981` with glow effects
- [ ] Serif hero headline (Playfair Display), sans/mono for UI (Inter / Geist Mono)
- [ ] Glassmorphism used sparingly — navbar and modals only
- [ ] GSAP scroll animations on landing page only (parallax, pinned sections, SplitText)
- [ ] Framer Motion spring animations for dashboard micro-interactions only
- [ ] Bento grid with cursor-tracking hover glows (Tier 3 / V2)
- [ ] Circular Confidence Ring (not a flat bar)
- [ ] Typewriter effect for AI explanations — first mount only
- [ ] Merchant controls everything — nothing auto-changes
- [ ] `prefers-reduced-motion` respected everywhere
- [ ] No scroll-jacking
- [ ] Particle canvas behind performance gate
- [ ] GSAP gated behind `gsap.matchMedia()` for mobile
- [ ] Trend chart lazy-loaded
- [ ] WCAG AA 4.5:1 contrast on all text
