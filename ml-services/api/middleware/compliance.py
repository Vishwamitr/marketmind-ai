from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class ComplianceHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-MarketMind-Disclaimer"] = "Not Investment Advice. Educational Purpose Only."
        return response
