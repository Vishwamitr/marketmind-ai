import logging
from pymongo import MongoClient
from news_pipeline.processor import NewsProcessor
from utils.config import Config
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_nlp_pipeline():
    logger.info("Starting NLP Pipeline Verification...")
    
    # 1. Connect to MongoDB
    client = MongoClient(Config.MONGODB_URL)
    db = client.get_database()
    collection = db.news_articles
    
    # 2. Insert dummy article
    dummy_article = {
        "title": "Market soars as tech stocks rally",
        "summary": "The S&P 500 reached new highs today driven by strong earnings from major tech companies.",
        "url": "http://test.com/market-rally",
        "published_at": "2026-02-15T10:00:00Z",
        "source": "Test Source"
    }
    
    # Clean up any previous test run
    collection.delete_many({"url": dummy_article["url"]})
    
    result = collection.insert_one(dummy_article)
    article_id = result.inserted_id
    logger.info(f"Inserted dummy article with ID: {article_id}")
    
    # 3. Run Processor
    logger.info("Running NewsProcessor...")
    processor = NewsProcessor()
    processor.process_new_articles()
    
    # 4. Verify Update
    updated_article = collection.find_one({"_id": article_id})
    
    if "sentiment" in updated_article:
        sentiment = updated_article["sentiment"]
        logger.info(f"SUCCESS: Article updated with sentiment: {sentiment}")
        print(f"Sentiment: {sentiment}")
        
        # Verify values
        if sentiment['label'] == 'positive' and sentiment['score'] > 0.5:
             logger.info("Verification Passed: Sentiment is positive as expected.")
        else:
             logger.warning(f"Verification Warning: Sentiment {sentiment} might not match expected 'positive'. check model.")
             
    else:
        logger.error("FAILURE: Article was NOT updated with sentiment.")

    # Cleanup
    collection.delete_one({"_id": article_id})

if __name__ == "__main__":
    verify_nlp_pipeline()
