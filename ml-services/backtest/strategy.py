from abc import ABC, abstractmethod
from dataclasses import dataclass
from backtest.simulator import MarketEvent

@dataclass
class Signal:
    symbol: str
    action: str # "BUY", "SELL", "HOLD"
    quantity: int = 0 # 0 means no action or use default sizing

class Strategy(ABC):
    @abstractmethod
    def on_data(self, event: MarketEvent) -> Signal:
        pass

class BuyAndHoldStrategy(Strategy):
    def __init__(self):
        self.brought = False

    def on_data(self, event: MarketEvent) -> Signal:
        if not self.brought:
            self.brought = True
            return Signal(symbol=event.symbol, action="BUY", quantity=0)
        return None

class SMACrossStrategy(Strategy):
    def on_data(self, event: MarketEvent) -> Signal:
        # Golden Cross: SMA50 > SMA200
        # For simplicity, if we are in BULLISH_TREND (Regime), we BUY.
        # Use RegimeDetector's output directly!
        
        from analysis.regime_detector import MarketRegime
        
        if event.regime == MarketRegime.BULLISH_TREND:
            return Signal(symbol=event.symbol, action="BUY", quantity=0) # Let engine size it
        elif event.regime == MarketRegime.BEARISH_TREND:
            return Signal(symbol=event.symbol, action="SELL", quantity=0) # Sell all
            
        return None
