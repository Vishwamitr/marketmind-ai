import logging
import pandas as pd
from data_pipeline.db_connector import DBConnector
import subprocess
import os
import sys

logger = logging.getLogger(__name__)

class RetrainingManager:
    def __init__(self, db=None):
        self.db = db if db else DBConnector()
        # Thresholds
        self.MAPE_THRESHOLD = 5.0 # Retrain if MAPE > 5%
        self.RMSE_THRESHOLD_MULTIPLIER = 1.5 # Retrain if RMSE > 1.5 * Moving Average

    def check_and_retrain(self, symbol):
        """
        Check predictions for the given symbol and trigger retraining if needed.
        """
        logger.info(f"Checking performance drift for {symbol}...")
        
        # 1. Get Recent Performance
        query = f"""
            SELECT model_name, evaluation_date, rmse, mape 
            FROM model_performance 
            WHERE symbol = '{symbol}' 
            ORDER BY evaluation_date DESC 
            LIMIT 5
        """
        with self.db.get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        if df.empty:
            logger.warning("No performance data found. Skipping check.")
            return

        latest = df.iloc[0]
        model_name = latest['model_name']
        latest_mape = float(latest['mape']) if latest['mape'] else 0.0
        latest_rmse = float(latest['rmse']) if latest['rmse'] else 0.0
        
        logger.info(f"Latest metrics for {model_name}: MAPE={latest_mape:.2f}%, RMSE={latest_rmse:.2f}")
        
        # 2. Check Thresholds
        trigger = False
        reason = ""
        
        if latest_mape > self.MAPE_THRESHOLD:
            trigger = True
            reason = f"MAPE ({latest_mape:.2f}%) > Threshold ({self.MAPE_THRESHOLD}%)"
            
        # We could also check moving average of RMSE
        if len(df) > 1:
            avg_rmse = df['rmse'][1:].mean() # Exclude latest
            if latest_rmse > avg_rmse * self.RMSE_THRESHOLD_MULTIPLIER:
                 trigger = True
                 reason = f"RMSE ({latest_rmse:.2f}) > 1.5x Historical Avg ({avg_rmse:.2f})"

        # 3. Trigger Retraining
        if trigger:
            logger.warning(f"RETRAINING TRIGGERED for {model_name} on {symbol}. Reason: {reason}")
            self._trigger_training_script(model_name, symbol)
        else:
            logger.info("Performance is within acceptable limits.")

    def _trigger_training_script(self, model_name, symbol):
        """
        Execute the training script for the specific model.
        """
        try:
            # Determine script based on model name
            # model_name in DB is usually 'Ensemble_Stacking' or 'XGBoost', etc.
            
            script_path = None
            if 'Ensemble' in model_name:
                script_path = "models.train_ensemble"
            elif 'XGBoost' in model_name:
                script_path = "models.train_xgboost"
            elif 'LSTM' in model_name or 'Transformer' in model_name:
                logger.info("Deep learning models are expensive to retrain automatically. Logging alert only.")
                return
            else:
                 # Default or Test models
                 logger.warning(f"No training script defined for model type: {model_name}")
                 return

            logger.info(f"Running {script_path} for {symbol}...")
            
            # Run as subprocess to avoid polluting current process state
            # Assumes running from ml-services root
            cmd = [sys.executable, "-m", script_path] 
            # Note: Scripts currently hardcode symbol='INFY', we might need to pass args.
            # But for this MVP, we just run the script.
            
            subprocess.run(cmd, check=True)
            logger.info("Retraining completed successfully.")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Retraining failed: {e}")
        except Exception as e:
            logger.error(f"Error triggering retraining: {e}")
