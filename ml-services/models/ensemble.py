import logging
import torch
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
from data_pipeline.db_connector import DBConnector
from models.lstm import StockLSTM
from models.transformer import StockTransformer
from models.data_loader import TimeSeriesDataset
from models.data_loader_tabular import TabularDataLoader
import os

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    def __init__(self, symbol='INFY', device='cpu'):
        self.symbol = symbol
        self.device = device
        # Use SGDRegressor for Online Learning support
        self.meta_model = SGDRegressor(max_iter=1000, tol=1e-3, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Base Models
        self.lstm = None
        self.transformer = None
        self.xgboost = None
        
        # Loaders (for feature info needed during loading)
        self.seq_len = 60
        
    def load_base_models(self):
        logger.info("Loading base models...")
        
        # 1. LSTM
        self.lstm = StockLSTM(input_dim=5, hidden_dim=64, num_layers=2, output_dim=1)
        self.lstm.load_state_dict(torch.load(f"checkpoints/lstm_{self.symbol}.pth", map_location=self.device))
        self.lstm.to(self.device).eval()
        
        # 2. Transformer
        self.transformer = StockTransformer(input_dim=5, d_model=64, nhead=4, num_layers=2)
        self.transformer.load_state_dict(torch.load(f"checkpoints/transformer_{self.symbol}.pth", map_location=self.device))
        self.transformer.to(self.device).eval()
        
        # 3. XGBoost
        self.xgboost = xgb.XGBRegressor()
        self.xgboost.load_model(f"checkpoints/xgboost_{self.symbol}.json")
        
        logger.info("Base models loaded.")

    def prepare_meta_dataset(self, lookback_days=365):
        # Returns X_meta (N, 3), y_meta (N,)
        
        # 1. Tabular Data (TARGET source)
        tab_loader = TabularDataLoader(self.symbol, lookback_days=lookback_days, lags=5)
        X_tab, y_tab = tab_loader.load_data() 
        if X_tab is None or len(X_tab) == 0:
            return None, None
            
        seq_loader = TimeSeriesDataset(self.symbol, seq_len=self.seq_len, lookback_days=lookback_days)
        
        # Determine timestamps for Tabular data
        # X_tab index is Timestamp
        
        # Fetch raw data to map Seq indices to Timestamps
        from data_pipeline.db_connector import DBConnector
        db = DBConnector()
        with db.get_connection() as conn:
            q = f"SELECT timestamp, close FROM stock_prices WHERE symbol = '{self.symbol}' AND timestamp > NOW() - INTERVAL '{lookback_days} days' ORDER BY timestamp ASC"
            df_raw = pd.read_sql(q, conn, index_col='timestamp')
            
        # Generate Predictions
        # XGB
        xgb_preds_series = pd.Series(self.xgboost.predict(X_tab), index=X_tab.index)
        
        preds_lstm = []
        preds_trans = []
        ts_list = []
        
        with torch.no_grad():
            for i in range(len(seq_loader)):
                X_seq, _ = seq_loader[i]
                X_seq = X_seq.unsqueeze(0).to(self.device) # (1, 60, 5)
                
                # Predict
                p_lstm = self.lstm(X_seq).item()
                p_trans = self.transformer(X_seq).item()
                
                # Inverse Transform
                p_lstm_real = seq_loader.inverse_transform(np.array([[p_lstm]]))[0]
                p_trans_real = seq_loader.inverse_transform(np.array([[p_trans]]))[0]
                
                preds_lstm.append(p_lstm_real)
                preds_trans.append(p_trans_real)
                
                # Determine Timestamp (Target is i + seq_len)
                target_idx = i + self.seq_len
                if target_idx < len(df_raw):
                    ts_list.append(df_raw.index[target_idx])

        lstm_series = pd.Series(preds_lstm, index=pd.to_datetime(ts_list))
        trans_series = pd.Series(preds_trans, index=pd.to_datetime(ts_list))
        
        # Handle Timezones
        if lstm_series.index.tz is None and xgb_preds_series.index.tz is not None:
             lstm_series.index = lstm_series.index.tz_localize(xgb_preds_series.index.tz)
             trans_series.index = trans_series.index.tz_localize(xgb_preds_series.index.tz)
        
        # Align
        df_meta = pd.DataFrame({
            'lstm': lstm_series,
            'trans': trans_series,
            'xgb': xgb_preds_series,
            'target': y_tab
        }).dropna()
        
        return df_meta[['lstm', 'trans', 'xgb']], df_meta['target']

    def train_meta(self):
        X, y = self.prepare_meta_dataset()
        if X is None or len(X) == 0:
            logger.error("No overlapping data for ensemble.")
            return
            
        logger.info(f"Training meta model on {len(X)} samples...")
        
        # Scale inputs
        X_scaled = self.scaler.fit_transform(X)
        self.meta_model.fit(X_scaled, y)
        self.is_fitted = True
        
        logger.info(f"Meta Model Coefficients: {self.meta_model.coef_}")
        logger.info(f"Intercept: {self.meta_model.intercept_}")

    def update_meta(self, X_new, y_new):
        """
        Online update of the meta model.
        X_new: shape (N, 3) or (3,) - [Pred_LSTM, Pred_Trans, Pred_XGB]
        y_new: shape (N,) or scalar - Actual Price
        """
        if not self.is_fitted:
            # First time fit if not exists
            self.scaler.partial_fit(X_new)
            X_scaled = self.scaler.transform(X_new)
            self.meta_model.partial_fit(X_scaled, y_new)
            self.is_fitted = True
        else:
            self.scaler.partial_fit(X_new)
            X_scaled = self.scaler.transform(X_new)
            self.meta_model.partial_fit(X_scaled, y_new)
            
        logger.info(f"Meta model updated. New Coefs: {self.meta_model.coef_}")

    def predict(self, X):
        """
        Predict using the meta model.
        X: (N, 3) used directly or aligned from base models (if not provided).
        For simplicity, this method assumes X is the (N,3) inputs.
        """
        if not self.is_fitted:
            logger.warning("Meta model not fitted. Returning None.")
            return None
        
        X_scaled = self.scaler.transform(X)
        return self.meta_model.predict(X_scaled)
        
    def save(self, path):
        # Save both model and scaler
        state = {
            'model': self.meta_model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted
        }
        joblib.dump(state, path)
        logger.info(f"Meta model saved to {path}")

    def load(self, path):
        if os.path.exists(path):
            state = joblib.load(path)
            # Check if old format (model only) or new format (dict)
            if isinstance(state, dict) and 'model' in state:
                self.meta_model = state['model']
                self.scaler = state.get('scaler', StandardScaler())
                self.is_fitted = state.get('is_fitted', True)
            else:
                # Legacy LinearRegression load
                logger.warning("Loaded legacy model format. SGDRegressor expected.")
                # We can't easily convert LinearRegression to SGDRegressor state.
                # Assuming this is a restart where we retrain.
                self.is_fitted = False
                
            logger.info(f"Meta model loaded from {path}")
        else:
            logger.warning(f"No checkpoint found at {path}")

