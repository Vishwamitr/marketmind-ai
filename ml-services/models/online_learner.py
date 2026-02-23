import logging
import pandas as pd
import numpy as np
from models.ensemble import EnsemblePredictor
from datetime import datetime
from data_pipeline.db_connector import DBConnector

logger = logging.getLogger(__name__)

class OnlineLearner:
    def __init__(self, symbol='INFY'):
        self.symbol = symbol
        self.predictor = EnsemblePredictor(symbol)
        self.db = DBConnector()
        
    def run_daily_update(self):
        """
        Perform an incremental update on the models using the latest available verified data.
        Typically run T+1 morning/EOD when T's close is final.
        We update using Data(T-1) -> Target(T).
        """
        logger.info(f"Running daily online update for {self.symbol}...")
        
        # 1. Load Models (Meta, LSTM, etc.)
        self.predictor.load_base_models()
        
        meta_path = f"checkpoints/ensemble_{self.symbol}.pkl"
        self.predictor.load(meta_path)
        
        if not self.predictor.is_fitted:
            logger.warning("Ensemble model not fitted. Skipping update. Consider full training.")
            return

        # 2. Get Latest Data Point (Target T)
        # We need the most recent row where we have both Inputs and Target.
        # We can reuse prepare_meta_dataset logic but limit to last N days to find new data.
        
        # Let's get "last known valid data"
        # We'll fetch last 100 days to ensure we find data even if gaps exist.
        X, y = self.predictor.prepare_meta_dataset(lookback_days=100)
        
        if X is None or len(X) == 0:
            logger.warning("No recent data for online update.")
            return

        # Ideally we track what we have already trained on.
        # But for 'Online Learning', seeing data twice in 'partial_fit' acts like higher weight.
        # We should try to feed only NEW data.
        # Since we don't track state, we will just feed the LAST row (Assuming run daily).
        
        X_latest = X.iloc[[-1]] 
        y_latest = y.iloc[[-1]]
        
        date_of_data = X_latest.index[0]
        logger.info(f"Updating model with data from {date_of_data} (Target: {y_latest.values[0]})")
        
        # 3. Update Meta Model
        self.predictor.update_meta(X_latest, y_latest)
        
        # 4. Update LSTM Model
        # We need the sequence ending at date_of_data for LSTM input
        # date_of_data is a Timestamp.
        try:
            # Fetch raw data for sequence from 3 tables and merge
            lookback = self.predictor.seq_len
            # We need slightly more than lookback to ensure overlap if using merge, but exact timestamp filtering should work.
            
            with self.db.get_connection() as conn:
                # 1. Prices
                q_p = f"SELECT timestamp, close, volume FROM stock_prices WHERE symbol = '{self.symbol}' AND timestamp <= '{date_of_data}' ORDER BY timestamp DESC LIMIT {lookback}"
                df_p = pd.read_sql(q_p, conn)
                
                # 2. Indicators
                q_i = f"SELECT timestamp, rsi_14 as rsi, macd FROM technical_indicators WHERE symbol = '{self.symbol}' AND timestamp <= '{date_of_data}' ORDER BY timestamp DESC LIMIT {lookback}"
                df_i = pd.read_sql(q_i, conn)
                
                # 3. Sentiment
                q_s = f"SELECT timestamp, sentiment_score as sentiment FROM market_sentiment WHERE symbol = '{self.symbol}' AND timestamp <= '{date_of_data}' ORDER BY timestamp DESC LIMIT {lookback}"
                df_s = pd.read_sql(q_s, conn)
            
            # Merge
            if not df_p.empty and not df_i.empty and not df_s.empty:
                df_seq = df_p.merge(df_i, on='timestamp', how='inner').merge(df_s, on='timestamp', how='inner')
                
                # Sort by timestamp ascending (chronological) for LSTM
                df_seq = df_seq.sort_values('timestamp')
                
                # Select features in order: close, volume, rsi, macd, sentiment
                # Ensure columns exist.
                features = ['close', 'volume', 'rsi', 'macd', 'sentiment']
                df_seq = df_seq[features]
                
                # Check length
                if len(df_seq) == lookback:
                    # Scale? LSTM was trained on Scaled Data.
                    # Problem: We don't have the scaler object used during LSTM training easily accessible!
                    # TimeSeriesDataset fits scaler on load.
                    # If we init TimeSeriesDataset, it refits scaler on current data.
                    # This might shift the distribution slightly but should be close.
                    
                    from models.data_loader import TimeSeriesDataset
                    import torch
                    
                    # Hack: Use TimeSeriesDataset to get scaler. 
                    # This is inefficient but works for now. 
                    # Ideally scaler should be saved with model.
                    ts_ds = TimeSeriesDataset(self.symbol, seq_len=lookback, lookback_days=lookback+20)
                    
                    # Transform our sequence using dataset's scaler
                    # We need to construct a DF matching what TimeSeriesDataset expects
                    # TimeSeriesDataset scales the whole 'data' array.
                    
                    # Let's hope scaling is consistent.
                    vals = df_seq.values
                    vals_scaled = ts_ds.scaler.transform(vals)
                    
                    X_tensor = torch.tensor(vals_scaled, dtype=torch.float32).unsqueeze(0).to(self.predictor.device)
                    y_tensor = torch.tensor([[y_latest.values[0]]], dtype=torch.float32).to(self.predictor.device)
                    
                    # Update LSTM
                    loss = self.predictor.lstm.update_model(X_tensor, y_tensor)
                    logger.info(f"LSTM updated. Loss: {loss:.6f}")
                    
                    # Save LSTM
                    torch.save(self.predictor.lstm.state_dict(), f"checkpoints/lstm_{self.symbol}.pth")
                
        except Exception as e:
            logger.error(f"Failed to update LSTM: {e}")

        # 5. Save Updated Meta Model
        self.predictor.save(meta_path)
        logger.info("Online update complete and models saved.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='INFY')
    args = parser.parse_args()
    
    learner = OnlineLearner(args.symbol)
    learner.run_daily_update()
