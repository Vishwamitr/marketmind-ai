import logging
import os
from models.ensemble import EnsemblePredictor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Trainer_Ensemble")

def train_ensemble(symbol='INFY'):
    predictor = EnsemblePredictor(symbol=symbol)
    
    # 1. Load Base Models
    try:
        predictor.load_base_models()
    except Exception as e:
        logger.error(f"Failed to load base models: {e}")
        return

    # 2. Train Meta Model
    # This internally aligns data and fits Linear Regression
    predictor.train_meta()
    
    # 3. Evaluate (on the same set for now to check fit, ideally separate val)
    X, y = predictor.prepare_meta_dataset()
    # Use predictor.predict to ensure scaling
    preds = predictor.predict(X)
    
    mse = mean_squared_error(y, preds)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y, preds)
    
    logger.info(f"Ensemble RMSE: {rmse:.4f}")
    logger.info(f"Ensemble MAE:  {mae:.4f}")
    
    # 4. Save
    os.makedirs("checkpoints", exist_ok=True)
    predictor.save(f"checkpoints/ensemble_{symbol}.pkl")

if __name__ == "__main__":
    train_ensemble(symbol='INFY')
