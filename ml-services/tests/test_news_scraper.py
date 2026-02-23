import unittest
from unittest.mock import MagicMock, patch
from news_pipeline.scraper import NewsScraper

class TestNewsScraper(unittest.TestCase):

    def setUp(self):
        patcher = patch('news_pipeline.scraper.MongoConnector')
        self.mock_mongo_cls = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Mock MongoConnector.get_db() to return a mock database
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_mongo_cls.get_db.return_value = self.mock_db
        self.mock_db.news_articles = self.mock_collection
        
        self.scraper = NewsScraper()

    @patch('feedparser.parse')
    def test_fetch_rss_feeds(self, mock_parse):
        # Mock feedparser response
        mock_entry = MagicMock()
        mock_entry.get.side_effect = lambda k, d=None: {
            "title": "Test News",
            "link": "http://example.com/news",
            "summary": "Summary",
            "published": "2023-01-01"
        }.get(k, d)
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_feed.feed.get.return_value = "Test Source"
        
        mock_parse.return_value = mock_feed

        # Run fetcher
        self.scraper.fetch_rss_feeds(["http://rss.url"])

        # Check DB interaction
        self.mock_collection.update_one.assert_called()

if __name__ == '__main__':
    unittest.main()
