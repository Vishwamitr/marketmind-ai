import logging
import pandas as pd
from datetime import datetime, timedelta
from backtest.simulator import MarketSimulator, MarketEvent
from backtest.portfolio import Portfolio
from backtest.strategy import Strategy, Signal, BuyAndHoldStrategy, SMACrossStrategy
from backtest import metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, symbol: str, start_date: datetime, end_date: datetime, strategy: Strategy, initial_capital: float = 100000.0, simulator: MarketSimulator = None):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.strategy = strategy
        self.portfolio = Portfolio(initial_capital)
        self.simulator = simulator if simulator else MarketSimulator()
        
    def run(self):
        logger.info(f"Starting backtest for {self.symbol}...")
        
        events = self.simulator.run_simulation(self.symbol, self.start_date, self.end_date)
        
        for event in events:
            # 1. Update Portfolio Value (Mark-to-Market)
            self.portfolio.update(event.timestamp, {event.symbol: event.close})
            
            # 2. Get Strategy Signal
            signal = self.strategy.on_data(event)
            
            # 3. Execute Trade (if any)
            if signal:
                # Simple quantity logic for MVP: Use fixed size or calculate max affordable
                qty = signal.quantity
                if qty == 0:
                    # Default: Use 10% of current cash
                    price = event.close
                    # Just a placeholder heuristic
                    if signal.action == "BUY":
                         # Invest 95% of available cash
                         qty = int((self.portfolio.cash * 0.95) / price)
                    elif signal.action == "SELL":
                         qty = self.portfolio.holdings.get(event.symbol, 0) # Sell all?
                
                # Update Signal Quantity
                signal.quantity = qty
                if qty > 0:
                    self.portfolio.execute_trade(signal, event.close)
                    logger.debug(f"Executed {signal.action} {qty} @ {event.close}")

        logger.info("Backtest completed.")
        return self._generate_report()

    def _generate_report(self):
        # Calculate Metrics
        perf = metrics.calculate_metrics(pd.DataFrame(self.portfolio.history))
        
        print("\n--- Backtest Performance Report ---")
        print(f"Strategy: {self.strategy.__class__.__name__}")
        print(f"Symbol: {self.symbol}")
        for k, v in perf.items():
            print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")
        print("-----------------------------------")
        
        return {
            "metrics": perf,
            "history": self.portfolio.history,
            "strategy": self.strategy.__class__.__name__,
            "symbol": self.symbol
        }


# --- Sample Strategies moved to backtest.strategy ---

if __name__ == "__main__":
    # Test Run
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365) # 1 Year Backtest
    
    # 1. Buy & Hold
    engine_bh = BacktestEngine('INFY', start_date, end_date, BuyAndHoldStrategy())
    engine_bh.run()
    
    # 2. SMA Cross (Regime Based)
    engine_sma = BacktestEngine('INFY', start_date, end_date, SMACrossStrategy())
    engine_sma.run()
