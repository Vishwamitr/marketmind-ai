import gymnasium as gym
from gymnasium import spaces
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TradingEnv(gym.Env):
    """
    Custom Trading Environment that follows gymnasium interface.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, df, initial_balance=10000, transaction_cost_pct=0.001):
        super(TradingEnv, self).__init__()
        
        self.df = df
        self.initial_balance = initial_balance
        self.transaction_cost_pct = transaction_cost_pct
        
        # Action space: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: 
        # [Balance, Shares_Held, Close, Volume, RSI, MACD, Sentiment]
        # We need to define bounds. 
        # Balance: 0 to Inf
        # Shares: 0 to Inf
        # Price/Indicators: -Inf to Inf (simplified)
        
        # Determine number of features from dataframe + account features
        # df features: close, volume, rsi_14, macd, sentiment_score (5 features)
        # account features: balance, shares_held (2 features)
        self.n_features = 5 + 2 
        
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.n_features,), dtype=np.float32
        )
        
        self.current_step = 0
        self.balance = initial_balance
        self.shares_held = 0
        self.net_worth = initial_balance
        self.max_steps = len(self.df) - 1

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.net_worth = self.initial_balance
        
        return self._next_observation(), {}

    def _next_observation(self):
        # Get market data for current step
        frame = self.df.iloc[self.current_step]
        
        # Create observation vector
        obs = np.array([
            self.balance,
            self.shares_held,
            frame['close'],
            frame['volume'],
            frame['rsi_14'],
            frame['macd'],
            frame['sentiment_score']
        ], dtype=np.float32)
        
        return obs

    def step(self, action):
        # Execute action
        self._take_action(action)
        
        self.current_step += 1
        
        # Check if done
        terminated = self.current_step >= self.max_steps
        truncated = False # Typically for time limits
        
        # Calculate Reward
        # Reward = Change in Net Worth
        current_price = self.df.iloc[self.current_step]['close']
        new_net_worth = self.balance + (self.shares_held * current_price)
        reward = new_net_worth - self.net_worth
        
        self.net_worth = new_net_worth
        
        observation = self._next_observation()
        info = {'net_worth': self.net_worth}
        
        return observation, reward, terminated, truncated, info

    def _take_action(self, action):
        current_price = self.df.iloc[self.current_step]['close']
        
        # 0 = Hold
        if action == 0:
            return
            
        # 1 = Buy (Buy as much as possible)
        # Simplified: Buy 1 share or Buy % of balance? 
        # Let's say we buy 1 share for simplicity in this V1
        if action == 1:
            cost = current_price * (1 + self.transaction_cost_pct)
            if self.balance >= cost:
                self.balance -= cost
                self.shares_held += 1
                
        # 2 = Sell (Sell all)
        # Simplified: Sell 1 share
        elif action == 2:
            if self.shares_held > 0:
                revenue = current_price * (1 - self.transaction_cost_pct)
                self.balance += revenue
                self.shares_held -= 1

    def render(self, mode='human', close=False):
        print(f'Step: {self.current_step}, Net Worth: {self.net_worth}')
