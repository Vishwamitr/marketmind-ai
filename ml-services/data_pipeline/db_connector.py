import psycopg2
from psycopg2 import pool
import logging
from contextlib import contextmanager
from utils.config import Config

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class DBConnector:
    """Singleton database connector using connection pooling."""
    
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            try:
                cls._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,
                    dsn=Config.TIMESCALE_URL
                )
                logger.info("Database connection pool created.")
            except Exception as e:
                logger.error(f"Error creating connection pool: {e}")
                raise e
        return cls._pool

    @classmethod
    @contextmanager
    def get_connection(cls):
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            yield conn
        except Exception:
            conn.rollback() # Rollback on error
            raise
        finally:
            conn.rollback() # Ensure transaction is closed/reset even if successful (idempotent if committed)
            pool.putconn(conn)

    @classmethod
    def close_pool(cls):
        if cls._pool:
            cls._pool.closeall()
            logger.info("Database connection pool closed.")

    @staticmethod
    def execute_query(query, params=None):
        """Execute a single query (INSERT/UPDATE/DELETE)."""
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(query, params)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Query execution failed: {e}")
                    raise e
