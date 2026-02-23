import logging
import pandas as pd
from datetime import datetime, timedelta
from pymongo import MongoClient
from data_pipeline.db_connector import DBConnector
from utils.config import Config

logger = logging.getLogger(__name__)

class SentimentScorer:
    """
    Aggregates news sentiment into time-series metrics.
    """

    def __init__(self):
        self.mongo_client = MongoClient(Config.MONGODB_URL)
        self.mongo_db = self.mongo_client.get_database()
        self.articles_collection = self.mongo_db.news_articles
        self.pg_db = DBConnector()

    def aggregate_daily_sentiment(self, symbol: str = None, days_back: int = 1):
        """
        Calculate daily sentiment score for a symbol.
        Score = (Sum(Pos * Conf) - Sum(Neg * Conf)) / Total_Articles
        """
        
        # Date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # MongoDB Query
        match_stage = {
            "published_at": {"$gte": start_date.isoformat()},
            "sentiment": {"$exists": True}
        }
        
        # Basic symbol filtering in MongoDB (heuristic, better if we have symbol field)
        # Assuming we might search by text or if we have a robust symbol tagger earlier
        # For now, let's assume articles might be tagged or we fetch all and group by simple keyword match?
        # To keep it simple for this phase: We will query ALL recent articles, and then in Python 
        # roughly group them if we can, or just calculate a "Global Market Sentiment" if symbol is difficult.
        # BUT, the Requirement is "for each stock". 
        # So let's rely on the text containing the symbol or name. 
        # Better: Feature 1.2 News Scraper should probably have tagged them.
        # If not, let's do a simple text search match here.
        
        if symbol:
            # Simple regex search for symbol in title/summary
            # Note: This is computationally expensive in Mongo without text index, but okay for prototype
            match_stage["$or"] = [
                {"title": {"$regex": symbol, "$options": "i"}},
                {"summary": {"$regex": symbol, "$options": "i"}}
            ]

        pipeline = [
            {"$match": match_stage},
            {"$project": {
                "date": {"$substr": ["$published_at", 0, 10]}, # Group by YYYY-MM-DD
                "sentiment": 1
            }},
            {"$group": {
                "_id": "$date",
                "articles": {"$push": "$sentiment"}
            }}
        ]
        
        results = list(self.articles_collection.aggregate(pipeline))
        
        if not results:
            logger.info(f"No sentiment data found for {symbol} in last {days_back} days.")
            return

        for day_res in results:
            date_str = day_res["_id"]
            sentiments = day_res["articles"]
            
            score, count = self._calculate_weighted_score(sentiments)
            
            # Store in TimescaleDB
            self._store_score(date_str, symbol if symbol else "MARKET", score, count)

    def _calculate_weighted_score(self, sentiment_list):
        """
        Calculate score from list of {label, score} dicts.
        """
        if not sentiment_list:
            return 0.0, 0
            
        total_score = 0.0
        count = len(sentiment_list)
        
        for item in sentiment_list:
            s_score = item.get('score', 0)
            label = item.get('label', 'neutral')
            
            if label == 'positive':
                total_score += s_score
            elif label == 'negative':
                total_score -= s_score
            # Neutral contributes 0 to numerator but increments denominator
            
        final_score = total_score / count if count > 0 else 0.0
        return final_score, count

    def _store_score(self, date_str, symbol, score, count):
        """
        Insert into Postgres.
        """
        query = """
            INSERT INTO market_sentiment (timestamp, symbol, sentiment_score, article_count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (timestamp, symbol) DO UPDATE SET
                sentiment_score = EXCLUDED.sentiment_score,
                article_count = EXCLUDED.article_count;
        """
        # Convert date string to timestamp (noon UTC)
        ts = f"{date_str} 12:00:00+00"
        
        try:
            with self.pg_db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (ts, symbol, score, count))
                conn.commit()
            logger.info(f"Stored sentiment for {symbol} on {date_str}: {score} ({count} articles)")
        except Exception as e:
            logger.error(f"Error storing sentiment: {e}")

if __name__ == "__main__":
    scorer = SentimentScorer()
    # Test run for "MARKET" (all articles) or specific symbol if we have one
    scorer.aggregate_daily_sentiment(symbol=None, days_back=30) 
