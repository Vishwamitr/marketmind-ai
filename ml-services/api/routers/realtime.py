from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websocket_manager import manager
import asyncio
import json
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

TICKER_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "KOTAKBANK", "LT", "HINDUNILVR", "SBIN", "BAJFINANCE",
]

async def simulate_market_data():
    """Broadcast real yfinance prices to /ws/ticker every 5 seconds."""
    while True:
        try:
            import yfinance as yf
            ns_syms = [f"{s}.NS" for s in TICKER_SYMBOLS]
            data = yf.download(ns_syms, period="2d", interval="1d", progress=False, auto_adjust=True)
            
            tick_data = []
            if data is not None and not data.empty:
                closes = data["Close"] if "Close" in data else data
                for sym, ns in zip(TICKER_SYMBOLS, ns_syms):
                    try:
                        col = closes[ns] if ns in closes.columns else None
                        if col is not None and len(col) >= 2:
                            price = float(col.iloc[-1])
                            prev  = float(col.iloc[-2])
                            chg   = round((price - prev) / prev * 100, 2) if prev else 0
                            tick_data.append({"symbol": sym, "price": round(price, 2), "change_pct": chg})
                    except Exception:
                        continue

            if tick_data:
                message = {
                    "type": "ticker_update",
                    "data": tick_data,
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(message, topic="TICKER")
        except Exception as e:
            logger.warning(f"Ticker fetch failed: {e}")
        await asyncio.sleep(5)


@router.websocket("/ws/ticker")
async def websocket_ticker(websocket: WebSocket):
    await manager.connect(websocket, topic="TICKER")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, topic="TICKER")


@router.websocket("/ws/stocks/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, topic=symbol)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, topic=symbol)


@router.websocket("/ws/news")
async def websocket_news_endpoint(websocket: WebSocket):
    topic = "NEWS"
    await manager.connect(websocket, topic=topic)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, topic=topic)
