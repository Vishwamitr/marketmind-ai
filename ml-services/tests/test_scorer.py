import unittest
from unittest.mock import MagicMock, patch
from analysis.sentiment_scorer import SentimentScorer

class TestSentimentScorer(unittest.TestCase):
    
    @patch('analysis.sentiment_scorer.MongoClient')
    @patch('analysis.sentiment_scorer.DBConnector')
    def test_calculate_weighted_score(self, mock_db, mock_mongo):
        scorer = SentimentScorer()
        
        # Test Case 1: Mixed sentiment
        sentiments = [
            {'label': 'positive', 'score': 0.9},
            {'label': 'negative', 'score': 0.8},
            {'label': 'neutral', 'score': 0.5}
        ]
        # (0.9 - 0.8) / 3 = 0.1 / 3 = 0.0333...
        score, count = scorer._calculate_weighted_score(sentiments)
        self.assertAlmostEqual(score, 0.03333333333333333)
        self.assertEqual(count, 3)

        # Test Case 2: All Positive
        sentiments_pos = [{'label': 'positive', 'score': 0.9}]
        score_pos, _ = scorer._calculate_weighted_score(sentiments_pos)
        self.assertEqual(score_pos, 0.9)

        # Test Case 3: Empty
        score_empty, count_empty = scorer._calculate_weighted_score([])
        self.assertEqual(score_empty, 0.0)
        self.assertEqual(count_empty, 0)

if __name__ == '__main__':
    unittest.main()
