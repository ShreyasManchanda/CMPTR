# DESIGN.md — CMPT Design System

This file is the single source of truth for color tokens, typography roles, spacing, and glass/motion rules.
It is derived from the project PRD (see `prd.md` §2).

## Tokens

/* Colors (use CSS custom properties in `src/styles/globals.css`) */
- `--bg-base`: #050505
- `--bg-surface-1`: #0A0A0A
- `--bg-surface-2`: #121212
- `--border`: rgba(255,255,255,0.06)
- `--border-glow`: rgba(52,211,153,0.15)
- `--text-primary`: #FAFAFA
- `--text-secondary`: #A1A1AA
- `--accent`: #10B981
- `--accent-glow`: rgba(16,185,129,0.25)
- `--error`: #EF4444
- `--warning`: #F59E0B
- `--glass-bg`: rgba(10,10,10,0.6)
- `--glass-border`: rgba(255,255,255,0.08)

## Typography

- Hero headline: `Playfair Display` (serif) — heavy display weight
- UI / body: `Inter` (sans-serif)
- Mono: `Geist Mono` (preferred) — fallback to `JetBrains Mono` if unavailable

## Radii & Elevation

- Cards: 16px
- Buttons: 8px (pill: 999px)
- Inputs: 12px
- Shadows: use `--shadow-card` and `--shadow-glow` tokens defined in `globals.css`

## Motion

- Landing page: GSAP + ScrollTrigger sequences (desktop only). Respect `prefers-reduced-motion`.
- Dashboard: Framer Motion for springy micro-interactions.

## Usage

1. Import tokens from `src/styles/globals.css`.
2. Use CSS variables for colors/spacing in all components.
3. Confirm `DESIGN.md` is present before authoring new components.

---

Notes:
- This file is intentionally minimal; the canonical token values live in `src/styles/globals.css`.
