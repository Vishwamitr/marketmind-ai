from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websocket_manager import manager
import asyncio
import random
import json
from datetime import datetime

router = APIRouter()

# Background task to simulate data pushes (for MVP demonstration)
async def simulate_market_data():
    """
    Simulates market data updates for a few symbols.
    """
    symbols = ["INFY", "TCS", "RELIANCE"]
    while True:
        # Pick a random symbol
        symbol = random.choice(symbols)
        price = 1000 + random.uniform(-10, 10) # Dummy price
        
        message = {
            "type": "price_update",
            "symbol": symbol,
            "price": round(price, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to subscribers of this symbol
        await manager.broadcast(message, topic=symbol)
        
        await asyncio.sleep(2) # Update every 2 seconds

@router.websocket("/ws/stocks/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, topic=symbol)
    try:
        while True:
            # Keep connection alive, maybe receive commands later
            # For now just wait for client to disconnect or send ping
            data = await websocket.receive_text()
            # If client sends "ping", respond "pong"?
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
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, topic=topic)
