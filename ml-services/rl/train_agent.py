import logging
import os
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from rl.trading_env import TradingEnv
from models.data_loader_tabular import TabularDataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Trainer_RL")

def train_rl_agent(symbol='INFY', total_timesteps=10000):
    # 1. Load Data (Reuse Tabular Loader)
    # We don't need lags for RL necessarily, as the agent can learn from state or we can use FrameStack.
    # But for now, let's just use the raw features provided by loader (without lags for simplicity, or with lags as state).
    # The Env expects specific columns. The loader returns X WITH lags.
    # Let's just use the raw dataframe logic inside loader? 
    # Actually, TabularDataLoader returns processed X, y. 
    # Let's instantiate loader but modify how we get data.
    
    loader = TabularDataLoader(symbol=symbol, lags=0) # No lags needed if we trust PPO or just want current state
    # load_data returns X, y. X has 'close', 'volume', etc.
    X, _ = loader.load_data()
    
    if X is None:
        logger.error("No data found.")
        return

    # Ensure columns match Env expectation
    # Env expects: ['close', 'volume', 'rsi_14', 'macd', 'sentiment_score']
    # + Balance/Shares which Env adds.
    needed_cols = ['close', 'volume', 'rsi_14', 'macd', 'sentiment_score']
    if not all(col in X.columns for col in needed_cols):
        logger.error(f"Missing columns in data. Have: {X.columns}")
        return
        
    df = X[needed_cols].reset_index(drop=True)
    
    # 2. Create Env
    # Vectorized env is required for stable_baselines3
    env = DummyVecEnv([lambda: TradingEnv(df)])
    
    # 3. Init Agent
    model = PPO('MlpPolicy', env, verbose=1)
    
    # 4. Train
    logger.info("Starting training...")
    model.learn(total_timesteps=total_timesteps)
    
    # 5. Save
    os.makedirs("checkpoints", exist_ok=True)
    save_path = f"checkpoints/ppo_{symbol}"
    model.save(save_path)
    logger.info(f"Model saved to {save_path}")

if __name__ == "__main__":
    train_rl_agent(symbol='INFY')
