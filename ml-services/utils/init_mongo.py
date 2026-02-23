from pymongo import MongoClient, ASCENDING, DESCENDING
import logging
from utils.config import Config

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

def init_mongo_schema():
    """Initialize MongoDB collections, indexes and validators."""
    try:
        client = MongoClient(Config.MONGODB_URL)
        db = client.get_database()
        
        # 1. News Articles Collection
        logger.info("Initializing 'news_articles' collection...")
        news = db.news_articles
        # Unique index on URL
        news.create_index([("url", ASCENDING)], unique=True)
        # Index on publication date for time-based queries
        news.create_index([("published_at", DESCENDING)])
        # Text index for search
        news.create_index([("title", "text"), ("summary", "text")])

        # 2. Logs/System Events Collection
        logger.info("Initializing 'system_logs' collection...")
        logs = db.system_logs
        # Index on timestamp
        logs.create_index([("timestamp", DESCENDING)])
        # Index on level and service
        logs.create_index([("level", ASCENDING), ("service", ASCENDING)])
        # TTL Index to auto-expire logs after 30 days
        logs.create_index([("timestamp", ASCENDING)], expireAfterSeconds=30*24*60*60)

        # 3. Model Metadata (Registry) - distinct from simple file storage
        logger.info("Initializing 'model_registry' collection...")
        models = db.model_registry
        models.create_index([("name", ASCENDING), ("version", ASCENDING)], unique=True)

        logger.info("MongoDB schema initialization complete.")

    except Exception as e:
        logger.error(f"MongoDB initialization failed: {e}")

if __name__ == "__main__":
    init_mongo_schema()
