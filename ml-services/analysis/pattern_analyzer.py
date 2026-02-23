import pandas as pd
import logging
from typing import List, Dict, Optional
from data_pipeline.db_connector import DBConnector
from utils.config import Config

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """
    Analyzes historical pattern frequency and distribution.
    """

    def __init__(self):
        self.db = DBConnector()

    def get_pattern_counts(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Get aggregated pattern counts, optionally filtered by symbol.
        
        Args:
            symbol (str, optional): Stock symbol to filter by.
        
        Returns:
            pd.DataFrame: DataFrame with columns [symbol, pattern_type, occurrence_count, last_observed, avg_confidence]
        """
        query = "SELECT * FROM pattern_stats"
        params = ()
        
        if symbol:
            query += " WHERE symbol = %s"
            params = (symbol,)
            
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql(query, conn, params=params)
                return df
        except Exception as e:
            logger.error(f"Error fetching pattern stats: {e}")
            return pd.DataFrame()

    def get_most_common_patterns(self, limit: int = 5) -> pd.DataFrame:
        """
        Get the most frequently occurring patterns across all stocks.
        """
        query = """
        SELECT pattern_type, SUM(occurrence_count) as total_count 
        FROM pattern_stats 
        GROUP BY pattern_type 
        ORDER BY total_count DESC 
        LIMIT %s
        """
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql(query, conn, params=(limit,))
                return df
        except Exception as e:
            logger.error(f"Error fetching common patterns: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    analyzer = PatternAnalyzer()
    print("Pattern Counts for INFY.NS:")
    print(analyzer.get_pattern_counts(symbol='INFY'))
    print("\nMost Common Patterns Global:")
    print(analyzer.get_most_common_patterns())
