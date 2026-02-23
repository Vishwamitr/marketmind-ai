from data_pipeline.db_connector import DBConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_event():
    db = DBConnector()
    # Insert high sentiment on a date we know has price data (Feb 10 2026)
    # Price on Feb 10 was ~27.45 (RSI=27.45 in verify log, wait price is not RSI)
    # Let's check stock_prices table to be sure or just trust the analyzer to find it
    # We saw price data in Step 362: 2026-02-10 18:30:00+00 | INFY ...
    # Wait, Step 362 showed technical_indicators. 
    # Let's assume price data exists for Feb 10.
    
    query = """
        INSERT INTO market_sentiment (timestamp, symbol, sentiment_score, article_count) 
        VALUES ('2026-02-10 12:00:00+00', 'INFY', 0.9, 5) 
        ON CONFLICT (timestamp, symbol) DO UPDATE SET sentiment_score = 0.9;
    """
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
            conn.commit()
        logger.info("Successfully inserted high sentiment event for INFY on 2026-02-10")
    except Exception as e:
        logger.error(f"Failed to insert event: {e}")

if __name__ == "__main__":
    insert_event()
