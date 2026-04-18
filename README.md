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
| 1 | **Crawler** | Accumulates product links from competitor store domains (capped to 5 per store) |
| 2 | **Scraper** | Extracts data via JSON-LD or **Markdown Fallback** (optimized for "Add to Bag") |
| 3 | **Normalise** | Automated currency conversion via **Frankfurter API** + symbol aliases |
| 4 | **Price** | Deterministic engine calculates market median and volatility position |
| 5 | **Rules** | Policy rules gate the recommendation (confidence/sample size thresholds) |
| 6 | **Ambiguity AI** | LLM resolves ambiguous store signals if the recommendation is `manual_review` |
| 7 | **Explanation AI** | **Always active.** Generates human-readable context for every recommendation |

---

## Quickstart

### Prerequisites

- **Python 3.11+** and **Node.js 18+**
- **Docker** (optional but recommended)
- API keys: **Gemini** and **Firecrawl**

### 1. Clone & Configure

```bash
git clone https://github.com/ShreyasManchanda/CMPT.git
cd CMPT
```

Set up your `.env`:
```env
FIRECRAWL_API_KEY=your_key
GEMINI_API_KEY=your_key
DATABASE_URL=postgresql://postgres:1234@localhost:5432/cmpt_db
```

### 2. Start the Backend with Docker

```bash
docker compose up -d
```

The system will start PostgreSQL and the FastAPI backend. Use the **init retry loop** logic to ensure a stable connection even if Postgres boots slowly. The backend will be accessible at `http://localhost:8000`.

### 3. Start the Frontend

In a new terminal window, start the React frontend:

```bash
cd frontend
npm install
npm run dev
```

The interface will be available at `http://localhost:5173`.

### 4. Run Tests

The test suite is unified and should be run from the `backend/` directory:

```bash
# Core logic & Math
python tests/test_pipeline.py

# Live Scraping & Crawling
python tests/test_scraper.py

# AI Agent Reasoning
python tests/test_agents.py
```

---

## API Endpoints

### `POST /discover-competitors`
Discover likely competitor storefronts from a product URL.

**Request:**
```json
{
  "product_url": "https://yourstore.com/p/1"
}
```

**Response:**
```json
{
  "status": "success",
  "product_name": "Your Product Name",
  "suggestions": [
    { "store": "competitor1.com", "url": "https://competitor1.com" },
    { "store": "competitor2.com", "url": "https://competitor2.com" }
  ]
}
```

### `POST /analyze`
Triggers an end-to-end pricing analysis.

**Request:**
```json
{
  "product_url": "https://yourstore.com/p/1",
  "competitor_urls": ["https://competitor.com"],
  "// Aliases": "my_product_url and competitor_store_urls also supported"
}
```

---

*Built by [Shreyas Manchanda](https://github.com/ShreyasManchanda)*
