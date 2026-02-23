import psycopg2
from utils.config import Config
from data_pipeline.db_connector import DBConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    queries = [
        """
        CREATE TABLE IF NOT EXISTS portfolio_balance (
            id SERIAL PRIMARY KEY,
            cash DOUBLE PRECISION NOT NULL DEFAULT 100000.0,
            last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS holdings (
            symbol VARCHAR(20) PRIMARY KEY,
            quantity INTEGER NOT NULL,
            avg_price DOUBLE PRECISION NOT NULL,
            last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            action VARCHAR(10) NOT NULL, -- BUY, SELL
            quantity INTEGER NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        # Initialize Balance if empty
        """
        INSERT INTO portfolio_balance (id, cash)
        SELECT 1, 100000.0
        WHERE NOT EXISTS (SELECT 1 FROM portfolio_balance WHERE id = 1);
        """
    ]

    try:
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                for q in queries:
                    cur.execute(q)
                conn.commit()
        logger.info("Portfolio tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
