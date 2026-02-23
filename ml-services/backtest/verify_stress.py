import logging
from datetime import datetime, timedelta
from backtest.engine import BacktestEngine, BuyAndHoldStrategy
from backtest.stress import FlashCrashScenario, StressedSimulator

logging.basicConfig(level=logging.INFO)

def verify():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    symbol = 'INFY'
    
    # 1. Normal Run
    print(">>> NORMAL RUN")
    engine_normal = BacktestEngine(symbol, start_date, end_date, BuyAndHoldStrategy())
    engine_normal.run()
    normal_final = engine_normal.portfolio.cash + list(engine_normal.portfolio.holdings.values())[0] * 0 # Approximate value check
    # Actually let's just look at metrics printed
    
    # 2. Crash Run
    print("\n>>> CRASH RUN (15th of month)")
    scenario = FlashCrashScenario(drop_pct=0.40) # 40% drop!
    stressed_sim = StressedSimulator(scenario)
    
    engine_crash = BacktestEngine(symbol, start_date, end_date, BuyAndHoldStrategy(), simulator=stressed_sim)
    engine_crash.run()

if __name__ == "__main__":
    verify()
