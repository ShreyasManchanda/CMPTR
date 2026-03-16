<div align="center">

# CMPT* — AI Competitive Pricing Intelligence Platform

**Crawls e-commerce stores, resolves ambiguous market signals with multi-agent reasoning, and generates actionable pricing insights — fully automated.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-000000?style=flat-square)](https://crewai.com)
[![Gemini](https://img.shields.io/badge/Gemini-LLM-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## What it does

Most pricing tools give you raw competitor data and leave interpretation to you. CMPT* goes further: it uses a **CrewAI multi-agent pipeline** to reason about that data — flagging pricing anomalies, resolving ambiguous signals (Is this a sale? A new baseline? A loss-leader?), and generating structured insights a pricing team can act on immediately.

You plug in a product category. The system crawls competitor listings, normalises the pricing data across inconsistent formats, passes it through an LLM-powered analysis layer, and returns a report with recommended pricing actions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CMPT* Pipeline                        │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Crawler    │───▶│  Normaliser  │───▶│  CrewAI      │  │
│  │  (e-commerce │    │  (pricing    │    │  Agents      │  │
│  │   stores)    │    │   data)      │    │              │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│                              ┌───────────────────┼────────┐ │
│                              │    Agent Network  │        │ │
│                              │                   ▼        │ │
│                              │  ┌─────────────────────┐  │ │
│                              │  │  Signal Resolver    │  │ │
│                              │  │  (Gemini LLM)       │  │ │
│                              │  └──────────┬──────────┘  │ │
│                              │             ▼             │ │
│                              │  ┌─────────────────────┐  │ │
│                              │  │  Pricing Analyst    │  │ │
│                              │  │  (rule engine +     │  │ │
│                              │  │   LLM reasoning)    │  │ │
│                              │  └──────────┬──────────┘  │ │
│                              └─────────────┼─────────────┘ │
│                                            ▼               │
│                              ┌─────────────────────────┐   │
│                              │    FastAPI REST Layer    │   │
│                              │    + Insight Report      │   │
│                              └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Agent roles:**
- **Crawler Agent** — discovers and scrapes competitor product listings
- **Normalisation Agent** — resolves inconsistent pricing formats, currency, bundle vs unit pricing
- **Signal Resolver** — uses Gemini LLM to classify ambiguous pricing moves (sale vs permanent drop vs promotional)
- **Pricing Analyst** — applies a rule-based volatility engine + LLM reasoning to generate recommended actions

---

## Results

| Metric | Value |
|---|---|
| Market signal ambiguity resolution | Automated via LLM — previously manual |
| Pricing report generation | End-to-end, no human-in-the-loop |
| Deployment | Production-ready REST API |

---

## Tech Stack

- **Agent orchestration**: CrewAI
- **LLM**: Google Gemini
- **Web crawling**: BeautifulSoup / Playwright
- **API**: FastAPI
- **Language**: Python 3.11

---

## Quickstart

### Prerequisites
- Python 3.11+
- Gemini API key

### Run locally

```bash
git clone https://github.com/ShreyasManchanda/CMPT
cd CMPT
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY
uvicorn app.main:app --reload
```

---

## API Usage

```bash
# Trigger a pricing analysis run
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"category": "wireless earbuds", "competitor_urls": ["..."]}'
```

Response:
```json
{
  "status": "complete",
  "signals_resolved": 14,
  "recommended_actions": [
    {
      "action": "hold",
      "reasoning": "Competitor drop is a flash sale — 72h pattern detected",
      "confidence": 0.87
    }
  ]
}
```

---

## Demo

> 📸 *Demo GIF coming soon — recording a full end-to-end analysis run.*

**What to expect:** Input a product category → watch the agent pipeline crawl, normalise, and reason → receive a structured pricing insight report.

---

## What to record for the demo GIF

---

## Project Structure

```
CMPTR/
├── backend/
│   ├── agent/
│   │   ├── ambiguity_agent.py
│   │   ├── explanation_agent.py
│   │   └── __init__.py
│   ├── config/
│   │   ├── agents.yaml
│   │   ├── config_loader.py
│   │   └── __init__.py
│   ├── normalizer/
│   │   ├── normalize_product.py
│   │   └── __init__.py
│   ├── pricing/
│   │   ├── pricing_engine.py
│   │   ├── rules_agent.py
│   │   └── __init__.py
│   ├── scraper/
│   │   ├── crawler.py
│   │   ├── scraper.py
│   │   └── __init__.py
│   └── utils/
├── .gitignore
├── LICENSE
└── README.md
```

---

## Roadmap

- [ ] Implementing Dockerfile for the code (Under Progress)
- [ ] Dashboard UI for pricing trends over time
- [ ] Slack/email alerting for significant competitor moves


---

*Built by [Shreyas Manchanda](https://github.com/ShreyasManchanda)*
