import feedparser
import requests
import logging
from datetime import datetime
import pymongo
from data_pipeline.mongo_connector import MongoConnector
from utils.config import Config

# Configure logger
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class NewsScraper:
    """Fetches news from various sources and stores in MongoDB."""

    def __init__(self):
        try:
            self.db = MongoConnector.get_db()
            self.collection = self.db.news_articles
            
            # Create unique index on URL to prevent duplicates at DB level
            self.collection.create_index([("url", pymongo.ASCENDING)], unique=True)
            logger.info("Connected to MongoDB and ensured indexes.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise here for now to allow partial testing if Mongo is down
            pass

    def fetch_rss_feeds(self, feed_urls: list):
        """
        Fetch and parse RSS feeds.
        """
        for url in feed_urls:
            logger.info(f"Fetching RSS feed: {url}")
            try:
                d = feedparser.parse(url)
                for entry in d.entries:
                    article = {
                        "title": entry.get("title"),
                        "link": entry.get("link"),
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published", datetime.now().isoformat()),
                        "source": d.feed.get("title", "Unknown RSS"),
                        "scraped_at": datetime.now()
                    }
                    self._save_article(article)
            except Exception as e:
                logger.error(f"Error parsing feed {url}: {e}")

    def fetch_newsapi(self, query: str = "Indian Stock Market"):
        """
        Fetch news from NewsAPI.
        """
        if not Config.NEWS_API_KEY:
            logger.warning("NewsAPI Key not found. Skipping.")
            return

        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={Config.NEWS_API_KEY}&language=en&sortBy=publishedAt"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("articles", []):
                    article = {
                        "title": item.get("title"),
                        "link": item.get("url"),
                        "summary": item.get("description", ""),
                        "published": item.get("publishedAt"),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "scraped_at": datetime.now()
                    }
                    self._save_article(article)
            else:
                logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")

    def _save_article(self, article: dict):
        """
        Save article to MongoDB, handling duplicates.
        """
        if not hasattr(self, 'collection'):
            logger.warning("MongoDB collection not available. Start Mongo container.")
            return

        try:
            # Simple deduplication based on URL
            self.collection.update_one(
                {"url": article["link"]},
                {"$setOnInsert": {
                    "title": article["title"],
                    "summary": article["summary"],
                    "published_at": article["published"],
                    "source": article["source"],
                    "crawled_at": article["scraped_at"]
                }},
                upsert=True
            )
            logger.debug(f"Saved/Updated article: {article['title']}")
        except Exception as e:
            logger.error(f"Error saving article: {e}")

if __name__ == "__main__":
    # Example usage
    scraper = NewsScraper()
    # Economic Times RSS (Example)
    rss_feeds = [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ]
    scraper.fetch_rss_feeds(rss_feeds)
