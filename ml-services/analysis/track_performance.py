import logging
import argparse
from datetime import datetime, timedelta
from analysis.performance_monitor import PerformanceMonitor
from models.ensemble import EnsemblePredictor
from data_pipeline.db_connector import DBConnector
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def track_performance(symbol='INFY', lookback_days=365):
    monitor = PerformanceMonitor()
    predictor = EnsemblePredictor(symbol=symbol)

    # 1. GENERATE PREDICTION (For T+1)
    # This assumes we want to run this daily to record TODAY's prediction for TOMORROW.
    try:
        logger.info(f"Generating prediction for {symbol}...")
        predictor.load_base_models()
        predictor.train_meta() # Fit meta model on recent data
        
        # We need to predict for "Next Day". 
        # EnsemblePredictor.prepare_meta_dataset gets historical X, y.
        # We need X_latest for T+1.
        
        # Let's add a method to EnsemblePredictor to get LATEST prediction?
        # Or just use the last row of prepared data?
        # TabularDataLoader returns X up to T (today) targetting T+1.
        # So the LAST row of X corresponds to Today.
        
        X, y = predictor.prepare_meta_dataset(lookback_days=lookback_days)
        if hasattr(X, 'iloc'):
             X_latest = X.iloc[[-1]] # Last row
        else:
             X_latest = X[-1:]

        # Predict
        predicted_price = predictor.meta_model.predict(X_latest)[0]
        
        # Date: If running today, this is prediction for tomorrow.
        # But wait, TabularLoader data:
        # X[T] uses close[T], close[T-1]... to predict target[T] which is close[T+1].
        # So if we have data up to Today (T), we can predict T+1.
        
        # We need the DATE of T.
        # In prepare_meta_dataset, we lost the index in the X returned to train_meta.
        # We need to fix EnsemblePredictor to allow predicting next day easily.
        
        # For now, let's assume T = today. Prediction is for T+1.
        prediction_date = (datetime.now() + timedelta(days=1)).date()
        
        monitor.record_prediction(
            model_name='Ensemble_Stacking',
            symbol=symbol,
            predicted_price=float(predicted_price),
            prediction_date=prediction_date
        )
        
    except Exception as e:
        logger.error(f"Error generating prediction: {e}")

    # 2. EVALUATE PERFORMANCE (For T-1, or whenever we last predicted)
    # We check if we have a prediction for "Yesterday" (or Today if we have EOD data).
    # If we run this after market close, we have Today's close.
    # So we can evaluate prediction made Yesterday for Today.
    
    evaluation_date = datetime.now().date() 
    # Check if we have data for 'evaluation_date' in stock_prices (i.e. Close price exists).
    
    logger.info(f"Evaluating performance for {evaluation_date}...")
    monitor.evaluate_performance(symbol, evaluation_date)
    
    # 3. CHECK FOR RETRAINING
    from analysis.retraining_manager import RetrainingManager
    retrainer = RetrainingManager()
    retrainer.check_and_retrain(symbol)

if __name__ == "__main__":
    track_performance()
