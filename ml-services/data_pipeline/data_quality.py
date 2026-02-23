import pandas as pd
import logging
from utils.config import Config
from data_pipeline.db_connector import DBConnector

logger = logging.getLogger(__name__)

class DataQualityService:
    """Checks data integrity and anomalies."""

    def __init__(self):
        self.db = DBConnector()

    def check_missing_values(self):
        """Check for missing timestamps in the last 24 hours."""
        query = """
        SELECT symbol, count(*) as count 
        FROM stock_prices 
        WHERE timestamp > NOW() - INTERVAL '1 day' 
        GROUP BY symbol;
        """
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql(query, conn)
                logger.info("Data counts for last 24h:\n" + str(df))
                
                # Check for low data volume (anomaly)
                low_volume = df[df['count'] < 10]
                if not low_volume.empty:
                    logger.warning(f"Low data volume detected for: {low_volume['symbol'].tolist()}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Data quality check failed: {e}")
            return False

    def check_price_anomalies(self, threshold_percent=0.1):
        """Check for price spikes > 10% in a single minute."""
        # Simple heuristic: compare close vs open
        query = """
        SELECT * FROM stock_prices 
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        AND ABS(close - open) / open > %s
        """
        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql(query, conn, params=(threshold_percent,))
                if not df.empty:
                    logger.warning(f"Price anomalies detected:\n{df[['timestamp', 'symbol', 'open', 'close']]}")
                    return False
                logger.info("No price anomalies detected.")
                return True
        except Exception as e:
            logger.error(f"Anomaly check failed: {e}")
            return False

if __name__ == "__main__":
    dq = DataQualityService()
    dq.check_missing_values()
    dq.check_price_anomalies()
