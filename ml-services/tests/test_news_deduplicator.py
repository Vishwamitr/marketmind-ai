import unittest
from unittest.mock import MagicMock, patch
from news_pipeline.news_deduplicator import NewsDeduplicator

class TestNewsDeduplicator(unittest.TestCase):

    @patch('news_pipeline.news_deduplicator.MongoClient')
    def setUp(self, mock_mongo):
        self.deduplicator = NewsDeduplicator()
        self.deduplicator.collection = MagicMock()

    def test_find_duplicates(self, ):
        # Mock articles in DB
        # Article 1 and 2 are similar
        articles = [
            {"_id": 1, "title": "Sensex crashes 500 points", "is_duplicate": False},
            {"_id": 2, "title": "Sensex drops 500 points today", "is_duplicate": False},
            {"_id": 3, "title": "Nifty reaches new all time high", "is_duplicate": False}
        ]
        
        self.deduplicator.collection.find.return_value = articles

        # Run deduplication
        self.deduplicator.find_duplicates(threshold=0.6)

        # Check if update_one was called for the duplicate
        # It should mark article 2 as duplicate of article 1 (or vice versa depending on loop)
        self.deduplicator.collection.update_one.assert_called()

if __name__ == '__main__':
    unittest.main()
