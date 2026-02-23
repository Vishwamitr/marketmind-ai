# MarketMind AI — Specification

> **Status**: FINALIZED
> **Last Updated**: 2026-02-16

## Overview
MarketMind AI is a comprehensive stock market prediction platform for the Indian market (NSE/BSE). It combines ML models, real-time data, sentiment analysis, and portfolio management into a unified platform.

## Core Requirements

### ML Services (Python/FastAPI)
- FastAPI server with JWT authentication, rate limiting, audit logging
- Data pipeline: stock_fetcher, real_time_fetcher, data_quality
- News pipeline: scraper, processor, deduplicator
- Analysis: sentiment (NLP), scorer, impact analysis
- Models: ensemble (XGBoost, LightGBM, LSTM), transformer
- Backtest engine for strategy validation
- RL trading agent
- WebSocket real-time market data
- SEBI compliance headers and disclaimers
- Comprehensive test suite (unit + integration + performance)

### Frontend (React/Vite/TypeScript)
- Dashboard with charts (Recharts)
- Portfolio management view
- News feed with sentiment indicators
- Real-time market data display
- Admin panel

### Backend (Express/TypeScript)
- API gateway between frontend and ML services
- User auth (JWT via Passport)
- PostgreSQL for relational data, MongoDB for documents, Redis for caching

### Infrastructure
- Docker Compose: TimescaleDB, PostgreSQL, MongoDB, Redis, Kafka, Zookeeper

## Quality Requirements
- All unit/mock tests pass without external dependencies
- Frontend builds successfully
- No deprecation warnings in core code
- Backend has functional source code
