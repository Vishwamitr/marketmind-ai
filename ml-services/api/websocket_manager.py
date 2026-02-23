from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Store active connections: symbol -> list of websockets
        # For general news, we can use a special key like 'NEWS'
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, topic: str):
        await websocket.accept()
        if topic not in self.active_connections:
            self.active_connections[topic] = []
        self.active_connections[topic].append(websocket)

    def disconnect(self, websocket: WebSocket, topic: str):
        if topic in self.active_connections:
            if websocket in self.active_connections[topic]:
                self.active_connections[topic].remove(websocket)
            if not self.active_connections[topic]:
                del self.active_connections[topic]

    async def broadcast(self, message: dict, topic: str):
        if topic in self.active_connections:
            for connection in self.active_connections[topic]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # If sending fails, we might want to disconnect, 
                    # but usually disconnect happens on receive/disconnect event
                    pass

manager = ConnectionManager()
