# Product

## Register

product

## Users

E-commerce merchants and pricing analysts who need competitor-aware pricing decisions without becoming data scientists. They paste a product URL and competitor store links, then need a clear action (Reduce / Hold / Review) with confidence and plain-language reasoning. Primary context: desk work in a browser, often comparing multiple stores under time pressure.

## Product Purpose

CMPT* is a competitive pricing intelligence console. It crawls competitor listings, normalizes prices, runs a deterministic pricing engine, and returns a recommended action with confidence score and AI-generated explanation. Success looks like: merchant understands what to do, why, and that nothing changes without their explicit approval.

## Brand Personality

Precise, calm, confident. Feels like a high-end developer tool (Linear / Vercel / Raycast caliber) rather than a marketing site. Voice is direct and technical without jargon walls; trust comes from explainability and human-in-the-loop control.

## Anti-references

- Generic purple-gradient AI SaaS landing pages
- Raw scraper UIs that dump tables with no recommendation
- Black-box "AI said so" pricing tools that auto-change prices
- Playful consumer fintech with bounce animations and emoji

## Design Principles

1. **Decision over data** — Surface the recommended action first; supporting metrics serve the decision, not the other way around.
2. **Explain before ask** — Every recommendation ships with confidence and plain-language reasoning so merchants can defend the choice.
3. **Merchant stays in control** — Nothing auto-applies; UI always frames advice, never silent mutation.
4. **Precision over spectacle** — Motion and chrome communicate state and trust; decoration that slows the task is cut.
5. **Confidence is first-class** — Ambiguity and low confidence are visible products, not error states to hide.

## Accessibility & Inclusion

Target WCAG AA. Honor `prefers-reduced-motion` for all GSAP/Framer/CSS motion. Maintain readable contrast on near-black surfaces (`#FAFAFA` on `#050505`, secondary text checked against surfaces). Keyboard-reachable primary flows (analyze form, FAQ, nav). No reliance on color alone for Reduce/Hold/Review states.
