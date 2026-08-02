<div align="center">

# CMPT* — AI Competitive Pricing Intelligence Platform

**Crawls e-commerce stores, resolves ambiguous market signals with multi-agent reasoning, and generates actionable pricing insights — fully automated.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-000000?style=flat-square)](https://crewai.com)
[![Gemini](https://img.shields.io/badge/Gemini-LLM-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## What It Does

Most pricing tools give you raw competitor data and leave interpretation to you. **CMPT\*** goes further: it uses a **CrewAI multi-agent pipeline** to reason about that data — flagging pricing anomalies, resolving ambiguous signals (*Is this a sale? A new baseline? A loss-leader?*), and generating structured insights a pricing team can act on immediately.

You paste a product URL and competitor store links. The system crawls competitor listings, normalises the pricing data across inconsistent formats, passes it through a deterministic pricing engine + LLM explanation layer, and returns a report with a **recommended action, confidence score, and plain-language explanation**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CMPT* Full-Stack                                  │
│                                                                             │
│    ┌──────────────────────────────────────────────────────────────────┐     │
│    │  FRONTEND  (React 18 + Vite)                                     │     │
│    │  ┌──────────┐  ┌────────────┐  ┌──────────────────────────────┐ │     │
│    │  │ Landing  │  │   Login    │  │      Dashboard               │ │     │
│    │  │  Page    │  │   Page     │  │  (React Query + Axios)       │ │     │
│    │  └──────────┘  └────────────┘  └──────────┬───────────────────┘ │     │
│    └───────────────────────────────────────────┼──────────────────────┘     │
│                                                │ REST API (JSON)            │
│    ┌───────────────────────────────────────────┼──────────────────────┐     │
│    │  BACKEND  (FastAPI + PostgreSQL)          │                      │     │
│    │                                           ▼                      │     │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │     │
│    │  │   Crawler    │─▶│  Normaliser  │─▶│  Pricing     │           │     │
│    │  │  (Firecrawl) │  │  (rules)     │  │  Engine      │           │     │
│    │  └──────────────┘  └──────────────┘  └──────┬───────┘           │     │
│    │                                             │                    │     │
│    │                      ┌──────────────────────┼──────────┐        │     │
│    │                      │   AI Agent Network   │          │        │     │
│    │                      │                      ▼          │        │     │
│    │                      │  ┌──────────────────────────┐   │        │     │
│    │                      │  │  Ambiguity Agent         │   │        │     │
│    │                      │  │  (Gemini LLM)            │   │        │     │
│    │                      │  └────────────┬─────────────┘   │        │     │
│    │                      │               ▼                 │        │     │
│    │                      │  ┌──────────────────────────┐   │        │     │
│    │                      │  │  Explanation Agent       │   │        │     │
│    │                      │  │  (Always Active)         │   │        │     │
│    │                      │  └──────────────────────────┘   │        │     │
│    │                      └─────────────────────────────────┘        │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│ └─────────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

| # | Stage | Description |
|---|---|---|
| 1 | **Discover** | Peer-brand search via Firecrawl + Gemini to suggest competitor storefronts |
| 2 | **Crawler** | Finds matching product links on each competitor domain |
| 3 | **Scraper** | Firecrawl v2 scrape (`product` / JSON extract + markdown fallback) |
| 4 | **Normalise** | Currency conversion via **Frankfurter API** + symbol aliases |
| 5 | **Price** | Deterministic engine calculates market median and volatility position |
| 6 | **Rules** | Policy rules gate the recommendation (confidence/sample size thresholds) |
| 7 | **Ambiguity AI** | LLM resolves ambiguous signals when the action is `manual_review` |
| 8 | **Explanation AI** | **Always active.** Plain-language context for every recommendation |

---

## Quickstart

### Prerequisites

- **Python 3.11+** and **Node.js 18+**
- **Docker** (recommended)
- API keys: **Gemini** and **Firecrawl**

### 1. Clone & Configure

```bash
git clone https://github.com/ShreyasManchanda/CMPTR.git
cd CMPTR
```

Copy `.env.example` → `.env` and set keys:

```env
FIRECRAWL_API_KEY=your_key
GEMINI_API_KEY=your_key
# Docker Compose uses host `db`. Outside Docker, use localhost:
DATABASE_URL=postgresql://postgres:1234@db:5432/cmpt_db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Frontend (optional): copy `frontend/.env.example` → `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=false
```

### 2. Start backend (Docker)

```bash
docker compose up -d
```

Starts PostgreSQL (`localhost:5432`) and the FastAPI API (`http://localhost:8000`). Health check: `GET /health`.

### 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

### 4. Run Tests

From `backend/`:

```bash
# Fast unit tests (no live API calls)
python -m pytest tests/test_unit.py -q

# Pipeline / agents / live scraper (need keys + network)
python tests/test_pipeline.py
python tests/test_agents.py
python tests/test_scraper.py
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness + DB check |
| `POST` | `/discover-competitors` | Suggest competitor storefronts from a product URL |
| `POST` | `/analyze` | Synchronous end-to-end analysis |
| `POST` | `/analyze/jobs` | Start async analysis (preferred for UI) |
| `GET` | `/analyze/jobs/{job_id}` | Poll async job status / result |
| `GET` | `/decisions` | Recent pricing decisions |
| `GET` | `/decisions/{id}` | Single decision detail |

Aliases accepted on analyze/discover bodies: `my_product_url` ↔ `product_url`, `competitor_store_urls` ↔ `competitor_urls`. Optional header `X-API-Key` when `CMPT_API_KEY` is set.

### `POST /discover-competitors`

```json
{
  "my_product_url": "https://yourstore.com/products/example"
}
```

### `POST /analyze/jobs`

```json
{
  "my_product_url": "https://yourstore.com/products/example",
  "competitor_store_urls": ["https://competitor.com"]
}
```

Interactive docs: **http://localhost:8000/docs**

---

*Built by [Shreyas Manchanda](https://github.com/ShreyasManchanda)*
