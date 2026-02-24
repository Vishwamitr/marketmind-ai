from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import stocks, news, portfolio, backtest, admin, monitor, system, realtime, auth, compliance
from api.routers import watchlist, recommendations, predictions
from api.routers import mutual_funds, options, alerts, journal
from strawberry.fastapi import GraphQLRouter
from api.graphql_schema import schema
from api.security import limiter, _rate_limit_exceeded_handler, RateLimitExceeded
from api.middleware.security import SecurityHeadersMiddleware
from api.middleware.compliance import ComplianceHeaderMiddleware
from api.middleware.audit import AuditMiddleware
import asyncio

@asynccontextmanager
async def lifespan(app):
    # Startup: start the simulation task
    asyncio.create_task(realtime.simulate_market_data())
    yield
    # Shutdown: cleanup if needed

app = FastAPI(title="MarketMind AI API", lifespan=lifespan)

# 1. Rate Limiting State
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Middlewares
app.add_middleware(AuditMiddleware)
app.add_middleware(ComplianceHeaderMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app = GraphQLRouter(schema)

# Include Routers
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(compliance.router, prefix="/api", tags=["Compliance"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(graphql_app, prefix="/graphql")
app.include_router(stocks.router, prefix="/api", tags=["Stocks"])
app.include_router(news.router, prefix="/api", tags=["News"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(backtest.router, prefix="/api", tags=["Backtest"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(monitor.router, prefix="/api", tags=["Monitor"])
app.include_router(realtime.router, tags=["Realtime"])
app.include_router(watchlist.router, prefix="/api", tags=["Watchlist"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(predictions.router, prefix="/api", tags=["Predictions"])
app.include_router(mutual_funds.router, prefix="/api", tags=["Mutual Funds"])
app.include_router(options.router, prefix="/api", tags=["Options"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(journal.router, prefix="/api", tags=["Journal"])

@app.get("/")
def read_root():
    return {"message": "MarketMind AI API is running"}
