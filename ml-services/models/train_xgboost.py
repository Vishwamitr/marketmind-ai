import logging
import argparse
from models.data_loader_tabular import TabularDataLoader
from models.xgboost_model import XGBoostPredictor
from sklearn.metrics import mean_squared_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Trainer_XGBoost")

def train_xgboost(symbol='INFY'):
    # 1. Load Data
    loader = TabularDataLoader(symbol=symbol, lags=5)
    X_train, y_train, X_val, y_val = loader.get_train_val_split()
    
    if X_train is None:
        logger.error("No data found.")
        return

    # 2. Init Model
    predictor = XGBoostPredictor(n_estimators=200, max_depth=5, learning_rate=0.05)
    
    # 3. Train
    predictor.train(X_train, y_train, X_val, y_val)
    
    # 4. Eval
    preds = predictor.predict(X_val)
    mse = mean_squared_error(y_val, preds)
    logger.info(f"Validation MSE: {mse:.6f}")
    
    # 5. Save
    predictor.save(f"checkpoints/xgboost_{symbol}.json")
    predictor.plot_importance(f"checkpoints/xgboost_{symbol}_importance.png")

if __name__ == "__main__":
    train_xgboost(symbol='INFY')
