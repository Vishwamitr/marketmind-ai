import logging
from data_pipeline.db_connector import DBConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    queries = [
        """
        CREATE TABLE IF NOT EXISTS model_predictions (
            id SERIAL PRIMARY KEY,
            model_name VARCHAR(50) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            predicted_value DOUBLE PRECISION NOT NULL,
            actual_value DOUBLE PRECISION, -- Nullable initially
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_preds_model_symbol_ts ON model_predictions (model_name, symbol, timestamp);
        """,
        """
        CREATE TABLE IF NOT EXISTS model_metrics (
            id SERIAL PRIMARY KEY,
            model_name VARCHAR(50) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            metric_name VARCHAR(50) NOT NULL, -- MAE, RMSE, DirectionalAccuracy
            value DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
        );
        """
    ]

    try:
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                for q in queries:
                    cur.execute(q)
                conn.commit()
        logger.info("Monitoring tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")

if __name__ == "__main__":
    init_db()
