import asyncio
import websockets
import json
import logging
from datetime import datetime
from utils.config import Config
from data_pipeline.db_connector import DBConnector

logger = logging.getLogger(__name__)

class RealTimeFetcher:
    """
    Handles real-time stock data ingestion via WebSocket.
    """

    def __init__(self, ws_url: str = None):
        self.ws_url = ws_url
        self.db = DBConnector()
        self.is_running = False

    async def connect(self):
        """Connect to WebSocket provider."""
        if not self.ws_url:
            logger.warning("No WebSocket URL provided. Starting simulation mode.")
            await self._simulate_stream()
            return

        logger.info(f"Connecting to WebSocket: {self.ws_url}")
        try:
            async with websockets.connect(self.ws_url) as websocket:
                self.is_running = True
                await self._listen(websocket)
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")

    async def _listen(self, websocket):
        """Listen for messages and process them."""
        while self.is_running:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                await self._process_data(data)
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed. Reconnecting...")
                break
            except Exception as e:
                logger.error(f"Error reading message: {e}")

    async def _process_data(self, data: dict):
        """Process incoming JSON data and store in DB."""
        # This method would need to be adapted to the specific provider's format
        # Example format: {'s': 'RELIANCE', 'p': 2500.50, 't': 1678888888}
        symbol = data.get('s')
        price = data.get('p')
        timestamp = datetime.fromtimestamp(data.get('t', datetime.now().timestamp()))
        
        if symbol and price:
            logger.debug(f"Received: {symbol} @ {price}")
            # In a real scenario, use a buffer/batch insert for high throughput
            # For now, we just log it or simulate insert
            # self.db.execute_query(...)
            pass

    async def _simulate_stream(self):
        """Simulate real-time data for testing."""
        logger.info("Starting real-time data simulation...")
        import random
        symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
        
        while True:
            symbol = random.choice(symbols)
            price = round(random.uniform(1000, 3000), 2)
            data = {'s': symbol, 'p': price, 't': datetime.now().timestamp()}
            await self._process_data(data)
            await asyncio.sleep(1) # Simulate 1 update per second

if __name__ == "__main__":
    fetcher = RealTimeFetcher()
    asyncio.run(fetcher.connect())
