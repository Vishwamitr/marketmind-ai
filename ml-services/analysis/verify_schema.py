import asyncio
import logging
from data_pipeline.db_connector import DBConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_tables():
    db = DBConnector()
    
    # 1. Create PREDICTIONS table
    create_predictions_query = """
    CREATE TABLE IF NOT EXISTS predictions (
        id SERIAL PRIMARY KEY,
        model_name VARCHAR(50) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        predicted_at TIMESTAMP NOT NULL,
        prediction_date DATE NOT NULL,
        predicted_price DECIMAL(10, 2) NOT NULL,
        actual_price DECIMAL(10, 2),
        error DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 2. Create MODEL_PERFORMANCE table
    create_performance_query = """
    CREATE TABLE IF NOT EXISTS model_performance (
        id SERIAL PRIMARY KEY,
        model_name VARCHAR(50) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        evaluation_date DATE NOT NULL,
        rmse DECIMAL(10, 4),
        mae DECIMAL(10, 4),
        mape DECIMAL(10, 4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(model_name, symbol, evaluation_date)
    );
    """
    
    try:
        logger.info("Verifying 'predictions' table...")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_predictions_query)
                conn.commit()
        logger.info("'predictions' table verified/created.")
        
        logger.info("Verifying 'model_performance' table...")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_performance_query)
                conn.commit()
        logger.info("'model_performance' table verified/created.")
        
    except Exception as e:
        logger.error(f"Error verifying schema: {e}")

if __name__ == "__main__":
    verify_tables()
