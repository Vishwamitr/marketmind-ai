# MarketMind AI — Roadmap

> **Milestone**: Fix All Issues & Complete Project
> **Created**: 2026-02-16

## Phase 1: Fix Frontend Build
**Status**: 🔲 Pending
**Goal**: Fix TailwindCSS v4 PostCSS configuration so frontend builds and runs.
**Must-Haves**:
- [ ] Install `@tailwindcss/postcss` and update `postcss.config.js`
- [ ] Remove deprecated `tailwindcss` direct PostCSS plugin usage
- [ ] `npm run build` succeeds without errors

---

## Phase 2: Fix ML Services Failing Tests
**Status**: 🔲 Pending
**Goal**: Fix all 5 failing unit/mock tests so full test suite passes without external services.
**Must-Haves**:
- [ ] `test_get_admin_stats` passes (add auth dependency override)
- [ ] `test_get_portfolio` passes (add auth dependency override)
- [ ] `test_login_user` passes (fix DBConnector mock pattern)
- [ ] `test_rate_limiting` passes (reset limiter state between tests)
- [ ] `test_process_articles` passes (fix mock target from MongoClient to MongoConnector)

---

## Phase 3: Fix Deprecation Warnings
**Status**: 🔲 Pending
**Goal**: Eliminate deprecation warnings from core code.
**Must-Haves**:
- [ ] Replace `@app.on_event("startup")` with lifespan handler
- [ ] Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`
- [ ] Replace `pd.read_sql()` with SQLAlchemy connectable (or suppress warning)

---

## Phase 4: Scaffold Backend Source Code
**Status**: 🔲 Pending
**Goal**: Create the Express/TypeScript backend with routes, middleware, and basic functionality.
**Must-Haves**:
- [ ] Entry point (`src/index.ts`) with Express server
- [ ] Auth middleware (JWT via passport-jwt)
- [ ] Proxy routes to ML services API
- [ ] Health check endpoint
- [ ] CORS, Helmet, rate limiting configured
- [ ] `npm run dev` starts the server
