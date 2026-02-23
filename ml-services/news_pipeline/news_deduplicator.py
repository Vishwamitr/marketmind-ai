from pymongo import MongoClient
import logging
import os
import sys
# Add parent directory to path to allow imports from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from difflib import SequenceMatcher
from utils.config import Config

# Configure logger
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class NewsDeduplicator:
    """Service to identify and merge duplicate news articles."""

    def __init__(self, db=None):
        try:
            if db:
                self.db = db
            else:
                self.client = MongoClient(Config.MONGODB_URL)
                self.db = self.client.get_database()
            
            self.collection = self.db.news_articles
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def find_duplicates(self, threshold=0.85):
        """
        Scan for duplicates using title similarity.
        
        Args:
            threshold (float): Similarity threshold (0-1).
        """
        articles = list(self.collection.find({}, {"title": 1, "_id": 1, "is_duplicate": 1}))
        total = len(articles)
        logger.info(f"Scanning {total} articles for duplicates...")

        duplicates_found = 0
        
        for i in range(total):
            if articles[i].get("is_duplicate"):
                continue

            for j in range(i + 1, total):
                if articles[j].get("is_duplicate"):
                    continue

                sim = SequenceMatcher(None, articles[i]["title"], articles[j]["title"]).ratio()
                
                if sim > threshold:
                    logger.info(f"Duplicate found: '{articles[i]['title']}' == '{articles[j]['title']}' ({sim:.2f})")
                    self._mark_as_duplicate(articles[j]["_id"], articles[i]["_id"])
                    duplicates_found += 1
        
        logger.info(f"Deduplication complete. Found {duplicates_found} duplicates.")

    def _mark_as_duplicate(self, duplicate_id, original_id):
        """
        Mark an article as a duplicate of another.
        """
        try:
            self.collection.update_one(
                {"_id": duplicate_id},
                {"$set": {
                    "is_duplicate": True,
                    "original_article_id": original_id
                }}
            )
        except Exception as e:
            logger.error(f"Error updating duplicate {duplicate_id}: {e}")

if __name__ == "__main__":
    dedup = NewsDeduplicator()
    dedup.find_duplicates()
