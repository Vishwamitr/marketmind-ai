import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

@dataclass
class Trade:
    timestamp: datetime
    symbol: str
    action: str
    quantity: int
    price: float
    fees: float

class Portfolio:
    def __init__(self, initial_capital: float = 100000.0, transaction_cost_pct: float = 0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings: Dict[str, int] = {} # Symbol -> Quantity
        self.transaction_cost_pct = transaction_cost_pct
        
        # History
        self.history: List[dict] = [] # List of daily snapshots
        self.trades: List[Trade] = []

    def update(self, timestamp: datetime, current_prices: Dict[str, float]):
        """
        Mark-to-market update. Records the total value of the portfolio at this timestamp.
        """
        holdings_value = 0.0
        for symbol, qty in self.holdings.items():
            if symbol in current_prices:
                holdings_value += qty * current_prices[symbol]
        
        total_value = self.cash + holdings_value
        
        self.history.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'holdings_value': holdings_value,
            'total_value': total_value
        })

    def execute_trade(self, signal, price: float):
        """
        Executes a signal at the given price.
        signal: Signal object (symbol, action, quantity)
        price: Execution price
        """
        if signal.action == "HOLD" or signal.quantity == 0:
            return

        symbol = signal.symbol
        quantity = signal.quantity
        cost = quantity * price
        fees = cost * self.transaction_cost_pct

        if signal.action == "BUY":
            total_cost = cost + fees
            if self.cash >= total_cost:
                self.cash -= total_cost
                self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
                self._log_trade(signal, price, fees)
            else:
                # print(f"Insufficient cash to buy {quantity} {symbol}")
                pass 

        elif signal.action == "SELL":
            current_qty = self.holdings.get(symbol, 0)
            if current_qty >= quantity:
                revenue = cost - fees
                self.cash += revenue
                self.holdings[symbol] -= quantity
                if self.holdings[symbol] == 0:
                    del self.holdings[symbol]
                self._log_trade(signal, price, fees)
            else:
                # print(f"Insufficient holdings to sell {quantity} {symbol}")
                pass

    def _log_trade(self, signal, price, fees):
        # We assume timestamp is tracked externally or passed in signal, 
        # but Signal struct doesn't have it. We might need to add it or infer.
        # For MVP, we won't strictly log timestamp in Trade struct here if not passed.
        # Let's blindly append.
        self.trades.append({
            'symbol': signal.symbol,
            'action': signal.action,
            'quantity': signal.quantity,
            'price': price,
            'fees': fees
        })
