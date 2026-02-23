from pymongo import MongoClient
import logging
from utils.config import Config

logger = logging.getLogger(__name__)

class MongoConnector:
    """Singleton MongoDB connector."""
    
    _client = None
    _db = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                cls._client = MongoClient(Config.MONGODB_URL)
                logger.info("MongoDB client created.")
            except Exception as e:
                logger.error(f"Error creating MongoDB client: {e}")
                raise e
        return cls._client

    @classmethod
    def get_db(cls):
        if cls._db is None:
            client = cls.get_client()
            cls._db = client.get_database() # Uses db from connection string
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB connection closed.")
