import logging
from datetime import datetime, timedelta
from data_pipeline.db_connector import DBConnector
from analysis.performance_monitor import PerformanceMonitor
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_db():
    db = DBConnector()
    monitor = PerformanceMonitor()
    
    # 1. Check for recent predictions (The one just generated)
    logger.info("Checking predictions table...")
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 5")
            rows = cur.fetchall()
            for row in rows:
                logger.info(f"Prediction Row: {row}")

    # 2. Insert Dummy Prediction for Yesterday to test Evaluation
    yesterday = (datetime.now() - timedelta(days=1)).date()
    symbol = 'INFY' # Matches what track_performance used
    
    # Check if we have price for yesterday
    price = monitor._get_actual_price(symbol, yesterday)
    if price is None:
        logger.warning(f"No price for {yesterday}. Finding latest available price date.")
        # Find latest date in stock_prices
        with db.get_connection() as conn:
             df = pd.read_sql(f"SELECT timestamp, close FROM stock_prices WHERE symbol='{symbol}' ORDER BY timestamp DESC LIMIT 1", conn)
        if not df.empty:
            target_date = df.iloc[0]['timestamp'].date()
            price = float(df.iloc[0]['close'])
            logger.info(f"Using {target_date} (Price: {price}) for testing.")
        else:
            logger.error("No data found at all.")
            return
    else:
        target_date = yesterday
        logger.info(f"Found price for {target_date}: {price}")

    # Insert Dummy Prediction for that date (Predicted Price = Actual + 10 error)
    dummy_pred = price + 10.0
    logger.info(f"Inserting dummy prediction for {target_date}: {dummy_pred}")
    
    # We insert it as if it was predicted day before target_date
    monitor.record_prediction(
        model_name='Test_Model',
        symbol=symbol,
        predicted_price=dummy_pred,
        prediction_date=target_date
    )
    
    # 3. Run Evaluation for target_date
    logger.info(f"Running evaluation for {target_date}...")
    monitor.evaluate_performance(symbol, target_date)
    
    # 4. Check model_performance
    logger.info("Checking model_performance table...")
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM model_performance ORDER BY id DESC LIMIT 5")
            rows = cur.fetchall()
            for row in rows:
                logger.info(f"Performance Row: {row}")
                
    # 5. Check predictions table update
    logger.info("Checking predictions table update...")
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM predictions WHERE model_name='Test_Model' AND prediction_date='{target_date}'")
            rows = cur.fetchall()
            for row in rows:
                logger.info(f"Updated Prediction Row: {row}")

if __name__ == "__main__":
    verify_db()
