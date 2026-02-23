import unittest
import pandas as pd
import numpy as np
from rl.trading_env import TradingEnv

class TestTradingEnv(unittest.TestCase):
    
    def setUp(self):
        # Create Dummy Data
        self.df = pd.DataFrame({
            'close': [100, 105, 110, 100],
            'volume': [1000, 1200, 1100, 1000],
            'rsi_14': [50, 55, 60, 45],
            'macd': [0.1, 0.2, 0.3, 0.1],
            'sentiment_score': [0.1, 0.5, 0.2, -0.1]
        })
        self.env = TradingEnv(self.df, initial_balance=1000)

    def test_reset(self):
        obs, info = self.env.reset()
        # Check shape: 7 features
        self.assertEqual(len(obs), 7)
        # Check initial balance
        self.assertEqual(obs[0], 1000) # Balance
        self.assertEqual(obs[1], 0)    # Shares

    def test_buy_step(self):
        self.env.reset()
        # Action 1 = Buy
        obs, reward, terminated, truncated, info = self.env.step(1)
        
        # Price at step 0 is 100.
        # Cost = 100 * 1.001 (0.1% fee) = 100.1
        # New Balance = 1000 - 100.1 = 899.9
        self.assertAlmostEqual(self.env.balance, 899.9)
        self.assertEqual(self.env.shares_held, 1)
        
        # Reward calculation:
        # Step moved to index 1. Price is 105.
        # Net Worth = 899.9 + (1 * 105) = 1004.9
        # Prev Net Worth = 1000.
        # Reward = 4.9
        self.assertAlmostEqual(reward, 4.9)
        self.assertFalse(terminated)

    def test_sell_step(self):
        self.env.reset()
        self.env.shares_held = 1
        self.env.balance = 0
        self.env.net_worth = 100 # Approx (if price was 100)
        
        # Action 2 = Sell
        # Step 0 price = 100
        obs, reward, terminated, truncated, info = self.env.step(2)
        
        # Revenue = 100 * (1 - 0.001) = 99.9
        self.assertAlmostEqual(self.env.balance, 99.9)
        self.assertEqual(self.env.shares_held, 0)

if __name__ == '__main__':
    unittest.main()
