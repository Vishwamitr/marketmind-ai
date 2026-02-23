import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error
from data_pipeline.db_connector import DBConnector

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.db = DBConnector()

    def record_prediction(self, model_name, symbol, predicted_price, prediction_date):
        """
        Store a new prediction in the database.
        prediction_date is typically T+1 (tomorrow) relative to when prediction is made.
        """
        query = """
        INSERT INTO predictions (model_name, symbol, predicted_at, prediction_date, predicted_price)
        VALUES (%s, %s, NOW(), %s, %s)
        """
        try:
            self.db.execute_query(query, (model_name, symbol, prediction_date, predicted_price))
            logger.info(f"Recorded prediction for {model_name} on {symbol} for {prediction_date}: {predicted_price}")
        except Exception as e:
            logger.error(f"Failed to record prediction: {e}")

    def evaluate_performance(self, symbol, evaluation_date=None):
        """
        Evaluate predictions for a given date (default: yesterday).
        Updates 'predictions' with actuals and 'model_performance' with metrics.
        """
        if evaluation_date is None:
            # Default to yesterday (since we need actual close price which happens at EOD)
            evaluation_date = (datetime.now() - timedelta(days=1)).date()
        
        logger.info(f"Evaluating performance for {symbol} on {evaluation_date}...")
        
        # 1. Get Actual Price
        actual_price = self._get_actual_price(symbol, evaluation_date)
        if actual_price is None:
            logger.warning(f"No actual price data for {symbol} on {evaluation_date}. Skipping.")
            return

        # 2. Get Predictions for that Date
        # We might have multiple predictions (e.g. from different models)
        predictions = self._get_predictions_for_date(symbol, evaluation_date)
        
        if not predictions:
            logger.warning(f"No predictions found for {symbol} on {evaluation_date}.")
            return

        # 3. Calculate Errors and Update DB
        for pred in predictions:
            pred_id = pred['id']
            model_name = pred['model_name']
            predicted_price = pred['predicted_price']
            
            error = actual_price - predicted_price
            abs_error = abs(error)
            sq_error = error ** 2
            
            # Update Prediction Record
            self._update_prediction_actual(pred_id, actual_price, error)
            
            # Aggregate Daily Metrics (Simple: 1 sample per day per model usually)
            # If we had intraday, we would aggregate. Here RMSE = ABS(Error) effectively.
            
            self._record_daily_performance(model_name, symbol, evaluation_date, 
                                         rmse=np.sqrt(sq_error), mae=abs_error, actual_price=actual_price)

    def _get_actual_price(self, symbol, date):
        query = f"SELECT close FROM stock_prices WHERE symbol = '{symbol}' AND date(timestamp) = '{date}'"
        with self.db.get_connection() as conn:
            df = pd.read_sql(query, conn)
        if not df.empty:
            return float(df.iloc[0]['close'])
        return None

    def _get_predictions_for_date(self, symbol, date):
        query = f"SELECT id, model_name, predicted_price FROM predictions WHERE symbol = '{symbol}' AND prediction_date = '{date}'"
        with self.db.get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.to_dict('records')

    def _update_prediction_actual(self, pred_id, actual, error):
        query = "UPDATE predictions SET actual_price = %s, error = %s WHERE id = %s"
        try:
            self.db.execute_query(query, (actual, error, pred_id))
        except Exception as e:
            logger.error(f"Failed to update prediction {pred_id}: {e}")

    def _record_daily_performance(self, model_name, symbol, date, rmse, mae, actual_price):
        mape = 0.0
        if actual_price != 0:
            mape = (mae / actual_price) * 100
            
        # Ensure native python types for psycopg2
        rmse = float(rmse)
        mae = float(mae)
        mape = float(mape)
            
        query = """
        INSERT INTO model_performance (model_name, symbol, evaluation_date, rmse, mae, mape)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (model_name, symbol, evaluation_date) 
        DO UPDATE SET rmse = EXCLUDED.rmse, mae = EXCLUDED.mae, mape = EXCLUDED.mape;
        """
        try:
            self.db.execute_query(query, (model_name, symbol, date, rmse, mae, mape))
            logger.info(f"Recorded performance for {model_name} on {symbol}: RMSE={rmse:.2f}, MAPE={mape:.2f}%")
        except Exception as e:
            logger.error(f"Failed to record performance: {e}")
