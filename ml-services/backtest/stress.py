import logging
import random
from abc import ABC, abstractmethod
from typing import Generator
from datetime import datetime, timedelta
from backtest.simulator import MarketEvent, MarketSimulator

logger = logging.getLogger(__name__)

class StressScenario(ABC):
    @abstractmethod
    def apply(self, event: MarketEvent) -> MarketEvent:
        """
        Modify the market event to simulate stress.
        """
        pass

class NormalScenario(StressScenario):
    def apply(self, event: MarketEvent) -> MarketEvent:
        return event

class FlashCrashScenario(StressScenario):
    """
    Simulates a sudden price drop on a random day.
    """
    def __init__(self, drop_pct: float = 0.10, crash_date: datetime = None):
        self.drop_pct = drop_pct
        self.crash_date = crash_date # If None, random? For reproducibility, better to specify or pick first.
        self.crashed = False

    def apply(self, event: MarketEvent) -> MarketEvent:
        # Simple logic: If date matches (or strictly just one random event), drop price
        # For this MVP, let's say we crash if the date matches specific logic or just deterministically crash on the middle of the range if not set.
        
        should_crash = False
        if self.crash_date:
            if event.timestamp.date() == self.crash_date.date():
                should_crash = True
        else:
            # Deterministic: Crash if day is 15th of month?
            if event.timestamp.day == 15 and not self.crashed:
                should_crash = True
                self.crashed = True # Single crash

        if should_crash:
            logger.info(f"FLASH CRASH triggered at {event.timestamp}!")
            # Modify prices
            event.open *= (1 - self.drop_pct)
            event.high *= (1 - self.drop_pct)
            event.low *= (1 - self.drop_pct)
            event.close *= (1 - self.drop_pct)
            # regime might change too, but let's stick to price shock for now
        
        return event

class HighVolatilityScenario(StressScenario):
    """
    Increases High-Low range to simulate volatility.
    """
    def __init__(self, multiplier: float = 2.0):
        self.multiplier = multiplier

    def apply(self, event: MarketEvent) -> MarketEvent:
        # Widen the High/Low range around the Close/Open
        mid = (event.high + event.low) / 2
        half_range = (event.high - event.low) / 2
        
        new_half_range = half_range * self.multiplier
        event.high = mid + new_half_range
        event.low = mid - new_half_range
        
        # Ensure consistency
        event.high = max(event.high, event.open, event.close)
        event.low = min(event.low, event.open, event.close)
        
        return event

class StressedSimulator(MarketSimulator):
    """
    Wraps MarketSimulator to apply a scenario.
    """
    def __init__(self, scenario: StressScenario):
        super().__init__()
        self.scenario = scenario

    def run_simulation(self, symbol: str, start_date: str, end_date: str) -> Generator[MarketEvent, None, None]:
        # Get simulation generator from parent
        # Note: calling super().run_simulation might fetch data.
        # We need to intercept the yielded events.
        
        # We can reuse the parent's logic if we could start it.
        # super().run_simulation is a generator function.
        iterator = super().run_simulation(symbol, start_date, end_date)
        
        for event in iterator:
            modified_event = self.scenario.apply(event)
            yield modified_event
