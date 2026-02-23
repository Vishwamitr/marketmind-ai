import logging
import torch
from transformers import pipeline
from utils.config import Config

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes text sentiment using FinBERT.
    """

    def __init__(self):
        logger.info("Loading FinBERT model...")
        try:
            # Check if GPU is available
            device = 0 if torch.cuda.is_available() else -1
            self.pipe = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=device)
            logger.info(f"FinBERT model loaded on device {device}.")
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            self.pipe = None

    def analyze_text(self, text: str) -> dict:
        """
        Analyze sentiment of the given text.
        
        Args:
            text (str): Input text (e.g., news headline/summary).
            
        Returns:
            dict: {'label': 'positive'|'negative'|'neutral', 'score': float}
        """
        if not self.pipe:
            logger.error("Model not loaded.")
            return {'label': 'neutral', 'score': 0.0}

        try:
            # Truncate text to 512 tokens approx (FinBERT limit)
            # Pipeline handles truncation automatically usually, but let's be safe with char limit
            result = self.pipe(text[:2000])[0] 
            return {
                'label': result['label'],
                'score': result['score']
            }
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {'label': 'neutral', 'score': 0.0}

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print(analyzer.analyze_text("Stocks rally as inflation data comes in lower than expected."))
    print(analyzer.analyze_text("Company reports massive loss for the quarter."))
