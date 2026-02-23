import unittest
from unittest.mock import MagicMock, patch
from analysis.sentiment import SentimentAnalyzer
from news_pipeline.processor import NewsProcessor

class TestSentimentAnalyzer(unittest.TestCase):

    @patch('analysis.sentiment.pipeline')
    def test_analyze_text(self, mock_pipeline):
        # Mock the pipeline return value
        mock_pipe_instance = MagicMock()
        mock_pipe_instance.return_value = [{'label': 'positive', 'score': 0.95}]
        mock_pipeline.return_value = mock_pipe_instance

        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_text("Stocks are up!")
        
        self.assertEqual(result['label'], 'positive')
        self.assertEqual(result['score'], 0.95)

    @patch('analysis.sentiment.pipeline')
    def test_analyze_error(self, mock_pipeline):
         # Test error handling
        mock_pipe_instance = MagicMock()
        mock_pipe_instance.side_effect = Exception("Model failed")
        mock_pipeline.return_value = mock_pipe_instance
        
        analyzer = SentimentAnalyzer()
        # Should handle initialization error or runtime error smoothly
        # Here we mock the pipe call raising exception
        analyzer.pipe.side_effect = Exception("Inference error")
        
        result = analyzer.analyze_text("Text")
        self.assertEqual(result['label'], 'neutral')
        self.assertEqual(result['score'], 0.0)

class TestNewsProcessor(unittest.TestCase):
    
    @patch('news_pipeline.processor.MongoConnector')
    @patch('news_pipeline.processor.SentimentAnalyzer')
    def test_process_articles(self, mock_analyzer_cls, mock_mongo):
        # Mock DB — NewsProcessor uses MongoConnector.get_db()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo.get_db.return_value = mock_db
        mock_db.news_articles = mock_collection
        
        # Mock articles found
        mock_collection.find.return_value.limit.return_value = [
            {'_id': '1', 'title': 'Good news', 'summary': 'Stocks up'}
        ]
        
        # Mock Analyzer
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_analyzer_instance.analyze_text.return_value = {'label': 'positive', 'score': 0.9}
        
        processor = NewsProcessor()
        processor.process_new_articles()
        
        # Verify bulk write called
        mock_collection.bulk_write.assert_called_once()

if __name__ == '__main__':
    unittest.main()
