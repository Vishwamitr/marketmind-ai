import xgboost as xgb
import matplotlib.pyplot as plt
import logging
import os

logger = logging.getLogger(__name__)

class XGBoostPredictor:
    def __init__(self, n_estimators=100, max_depth=3, learning_rate=0.1):
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            objective='reg:squarederror',
            n_jobs=-1
        )
        
    def train(self, X_train, y_train, X_val=None, y_val=None):
        logger.info("Training XGBoost model...")
        
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_train, y_train), (X_val, y_val)]
            
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=10
        )
        
    def predict(self, X):
        return self.model.predict(X)
        
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save_model(path)
        logger.info(f"Model saved to {path}")
        
    def load(self, path):
        self.model.load_model(path)
        logger.info(f"Model loaded from {path}")
        
    def plot_importance(self, output_path='feature_importance.png'):
        plt.figure(figsize=(10, 8))
        xgb.plot_importance(self.model, max_num_features=20)
        plt.title("XGBoost Feature Importance")
        plt.tight_layout()
        plt.savefig(output_path)
        logger.info(f"Feature importance plot saved to {output_path}")
        plt.close()
