import logging
from pymongo import UpdateOne
from data_pipeline.db_connector import DBConnector
from data_pipeline.mongo_connector import MongoConnector
from analysis.sentiment import SentimentAnalyzer
from utils.config import Config

logger = logging.getLogger(__name__)

class NewsProcessor:
    """
    Processes news articles: extracts sentiment and updates DB.
    """

    def __init__(self, db=None, analyzer=None):
        # We need direct mongo access, reusing Config for URL
        print(f"DEBUG: Init called with db={type(db)}, analyzer={type(analyzer)}")
        self.db = db if db else MongoConnector.get_db()
        self.collection = self.db.news_articles
        self.analyzer = analyzer if analyzer else SentimentAnalyzer()

    def process_new_articles(self, limit: int = 50):
        """
        Fetch articles without sentiment and process them.
        """
        # Find articles where 'sentiment' field does not exist
        query = {"sentiment": {"$exists": False}}
        articles = list(self.collection.find(query).limit(limit))
        
        if not articles:
            logger.info("No new articles to process.")
            return

        logger.info(f"Processing {len(articles)} articles...")
        operations = []

        for article in articles:
            # Combine title and summary for better context
            text = f"{article.get('title', '')}. {article.get('summary', '')}"
            result = self.analyzer.analyze_text(text)
            
            # Prepare bulk update
            operations.append(
                UpdateOne(
                    {"_id": article["_id"]},
                    {"$set": {"sentiment": result}}
                )
            )

        if operations:
            result = self.collection.bulk_write(operations)
            logger.info(f"Updated {result.modified_count} articles with sentiment.")

if __name__ == "__main__":
    processor = NewsProcessor()
    processor.process_new_articles()
