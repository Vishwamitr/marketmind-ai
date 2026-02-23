<div align="center">

# 🧠 MarketMind AI

### *The AI-Powered Trading Intelligence Platform for Indian Markets*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript)](https://typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

> **MarketMind AI** is a full-stack, production-grade trading analytics platform built for the Indian markets (NSE/BSE). It combines machine learning models, real-time market data, options analytics, and AI-generated signals in a beautiful dark-mode interface.

<br/>

```
╔══════════════════════════════════════════════════════════╗
║  📈 Live Charts   🤖 AI Signals   🎯 Options Chain       ║
║  💼 Portfolio     🔔 Alerts       🌡️ Heatmap             ║
║  🧮 Position Calc 📊 Screener     📰 News Sentiment       ║
╚══════════════════════════════════════════════════════════╝
```

</div>

---

## ✨ Features at a Glance

### 📊 Market Intelligence
| Feature | Description |
|---------|-------------|
| **📈 Advanced Charts** | Candlestick, volume, RSI, MACD with 1D/1W/1M/6M/1Y timeframes |
| **🌡️ Market Heatmap** | Finviz-style sector treemap, color-coded by daily change |
| **📋 Smart Screener** | Real-time NIFTY 50 screener with RSI, change %, volume — batch optimized |
| **📰 News & Sentiment** | Scraped headlines with AI sentiment scoring per stock |
| **⏰ Market Hours Widget** | Live status for NSE, BSE, NYSE, NASDAQ, London, Tokyo |

### 🤖 AI & Machine Learning
| Feature | Description |
|---------|-------------|
| **🧠 AI Signal Cards** | Buy/Sell/Hold signals with confidence score, entry/SL/target levels |
| **🔮 Price Predictions** | LSTM + Transformer + XGBoost ensemble model predictions |
| **🎯 Options Analytics** | Greeks (Delta, Gamma, Theta, Vega), OI analysis, Max Pain, PCR |
| **📈 IV Smile Chart** | Call/Put implied volatility curve with ATM marker and skew metric |
| **🔄 Online Learning** | Models retrain automatically on new market data |

### 💼 Portfolio & Risk
| Feature | Description |
|---------|-------------|
| **📊 Portfolio Analytics** | Sharpe ratio, Beta, Max Drawdown, Win Rate vs NIFTY 50 benchmark |
| **📋 Sector Allocation** | Donut chart of holdings by sector |
| **🧮 Position Calculator** | Risk-based position sizing for stocks, futures & options |
| **📋 Stock Comparison** | Side-by-side normalized performance for 2–4 stocks |
| **🔔 Price Alerts** | Set price/RSI/volume alerts with browser push notifications |

### 🛡️ Platform & Security
| Feature | Description |
|---------|-------------|
| **🔐 JWT Auth** | Secure login with access + refresh token flow |
| **🚦 Rate Limiting** | SlowAPI-based per-IP rate limiting |
| **📜 SEBI Compliance** | Risk disclaimers, audit logging, compliance headers |
| **⚡ WebSockets** | Real-time simulated market data streaming |
| **🐍 GraphQL** | Strawberry-powered GraphQL API alongside REST |

---

## 🗂️ Project Structure

```
marketmind-ai/
├── 🎨 frontend/                  # React + TypeScript + Vite
│   └── src/
│       ├── components/           # Dashboard, Sidebar, Charts, MarketHoursWidget
│       └── pages/                # 16 pages (Analysis, Portfolio, Options...)
│
├── 🐍 ml-services/               # FastAPI Python backend
│   ├── api/
│   │   ├── main.py               # App entrypoint, middleware, routers
│   │   ├── routers/              # 15 API routers
│   │   │   ├── stocks.py         # Market data, screener, hours
│   │   │   ├── options.py        # Chain, Greeks, IV Smile, Max Pain
│   │   │   ├── portfolio.py      # Holdings, analytics, risk metrics
│   │   │   ├── alerts.py         # Price alert CRUD + checker
│   │   │   ├── recommendations.py# AI signal generation
│   │   │   └── ...12 more
│   │   └── middleware/           # Security, audit, compliance
│   ├── models/                   # LSTM, Transformer, XGBoost, Ensemble
│   ├── analysis/                 # Indicators, patterns, sentiment
│   ├── backtest/                 # Strategy engine + stress testing
│   ├── data_pipeline/            # Ingestion, DB, real-time feeds
│   └── tests/                   # Unit, integration, performance (Locust)
│
└── 🏗️ infrastructure/
    ├── docker-compose.yml
    └── postgres_schema.sql
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Git**

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Vishwamitr/marketmind-ai.git
cd marketmind-ai
```

---

### 2️⃣ Backend Setup

```bash
cd ml-services

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Initialize the databases:**
```bash
# Portfolio DB
python data_pipeline/init_portfolio_db.py

# Monitoring DB
python data_pipeline/init_monitoring_db.py

# Ingest initial market data
python data_pipeline/ingest_all.py
```

**Start the API server:**
```bash
uvicorn api.main:app --reload --port 8000
```

The API will be live at → `http://localhost:8000`
Interactive docs at → `http://localhost:8000/docs`

---

### 3️⃣ Frontend Setup

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be live at → `http://localhost:5173`

---

## 🗺️ Navigation Guide

| Page | Route | Description |
|------|-------|-------------|
| 🏠 Dashboard | `/` | Market overview, AI signals, global indices |
| 📈 Analysis | `/analysis/RELIANCE` | Full stock analysis with charts + AI |
| 💼 Portfolio | `/portfolio` | Holdings + risk analytics tab |
| ⭐ Watchlist | `/watchlist` | Tracked stocks with real-time prices |
| 🤖 AI Signals | `/recommendations` | All AI buy/sell/hold signals |
| 🔔 Alerts | `/alerts` | Create & manage price alerts |
| 🎯 Options | `/options` | Options chain + IV Smile chart |
| 📊 Screener | `/screener` | Filter stocks by RSI, momentum, volume |
| 🌡️ Heatmap | `/heatmap` | Sector-based market heatmap |
| 📰 News | `/news` | Headlines with sentiment analysis |
| 📋 Compare | `/compare` | Compare 2–4 stocks side-by-side |
| 🧮 Position Calc | `/position-calc` | Risk-based position sizing |
| 🏦 Mutual Funds | `/mutual-funds` | MF explorer with NAV history |
| ⏮️ Backtest | `/backtest` | Strategy backtesting engine |
| 📡 Monitor | `/monitor` | ML model performance monitoring |
| 🛡️ Admin | `/admin` | System stats, user management |

---

## 🔌 Key API Endpoints

```http
# Market Data
GET  /api/market/overview        → Dashboard summary
GET  /api/market/screener        → Batch NIFTY 50 data (optimized)
GET  /api/market/hours           → Global market status (60s cache)
GET  /api/market/history/{sym}   → OHLCV price history

# Options
GET  /api/options/chain/{sym}    → Full options chain with Greeks
GET  /api/options/iv-smile/{sym} → IV Smile/Skew data
GET  /api/options/max-pain/{sym} → Max pain strike

# AI & Predictions
GET  /api/recommend/{symbol}     → AI signal with confidence
GET  /api/predict/{symbol}       → Price target prediction

# Portfolio
GET  /api/portfolio              → Holdings & P&L
GET  /api/portfolio/analytics    → Risk metrics (Sharpe, Beta, Drawdown)

# Alerts
POST /api/alerts                 → Create alert
GET  /api/alerts                 → List active alerts
POST /api/alerts/check           → Check & trigger alerts
```

---

## 🧪 Running Tests

```bash
cd ml-services

# Activate venv first
venv\Scripts\activate  # Windows

# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=api --cov-report=html

# Performance test (Locust)
locust -f tests/locustfile.py --host=http://localhost:8000
```

---

## 🛠️ Tech Stack

### Frontend
```
React 19 · TypeScript · Vite · Recharts · Lucide React
React Router · Axios · CSS Variables (dark theme)
```

### Backend
```
FastAPI · Uvicorn · SQLite · yfinance · pandas · numpy
strawberry (GraphQL) · slowapi · python-jose (JWT)
scikit-learn · PyTorch · XGBoost · stable-baselines3
```

### ML Models
```
LSTM (PyTorch)         → Sequence price prediction
Transformer (PyTorch)  → Attention-based forecasting
XGBoost                → Tabular feature prediction
Ensemble               → Weighted model combination
PPO (RL)               → Reinforcement learning agent
```

---

## 🗺️ Roadmap

### ✅ Phase 1 — Core Platform
- Advanced charting, options chain, AI signals, portfolio analytics, market hours, screener optimization

### ✅ Phase 2 — Professional Polish
- Price alerts, market heatmap, IV smile chart, position calculator, stock comparison, CSS animations

### 🔜 Phase 3 — Advanced Intelligence *(Coming Next)*
- 🧠 **GPT-powered Trade Journal** — AI-written analysis for every trade
- 📡 **WebSocket Live Prices** — Tick-by-tick real-time streaming to dashboard
- 🗓️ **Earnings Calendar** — Upcoming results with analyst expectations vs actuals
- 🌊 **Options Flow Scanner** — Unusual options activity / whale detection
- 📦 **Strategy Builder UI** — Visual drag-and-drop strategy composer
- 📱 **Mobile-Responsive Layout** — Full PWA support

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/awesome-feature`
3. Commit: `git commit -m "feat: add awesome feature"`
4. Push: `git push origin feature/awesome-feature`
5. Open a Pull Request

---

## ⚠️ Disclaimer

> **MarketMind AI is for educational and research purposes only.** All AI signals, recommendations, and predictions are generated by machine learning models and do **not** constitute financial advice. Always consult a SEBI-registered investment advisor before making trading decisions. Past performance does not guarantee future results.

---

<div align="center">

Made with ❤️ for the Indian markets

⭐ **Star this repo** if you find it useful!

[![GitHub stars](https://img.shields.io/github/stars/Vishwamitr/marketmind-ai?style=social)](https://github.com/Vishwamitr/marketmind-ai/stargazers)

</div>
