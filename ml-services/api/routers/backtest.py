from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backtest.engine import BacktestEngine
from backtest.strategy import BuyAndHoldStrategy, SMACrossStrategy
from backtest.stress import FlashCrashScenario, StressedSimulator

router = APIRouter()

class BacktestRequest(BaseModel):
    symbol: str
    start_date: str # YYYY-MM-DD
    end_date: str   # YYYY-MM-DD
    initial_capital: float = 100000.0
    strategy: str # 'BuyAndHold', 'SMACross'
    scenario: Optional[str] = None # 'None', 'FlashCrash'

@router.post("/backtest/run")
def run_backtest(request: BacktestRequest):
    try:
        # 1. Parse Dates
        start_dt = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        # 2. Select Strategy
        if request.strategy == "BuyAndHold":
            strategy = BuyAndHoldStrategy()
        elif request.strategy == "SMACross":
            strategy = SMACrossStrategy()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")
            
        # 3. Configure Simulator (Stress Test)
        simulator = None
        if request.scenario == "FlashCrash":
            # Hardcoded 20% drop for now, or could make it configurable
            scenario = FlashCrashScenario(drop_pct=0.20)
            simulator = StressedSimulator(scenario)
            
        # 4. Run Engine
        engine = BacktestEngine(
            symbol=request.symbol,
            start_date=start_dt,
            end_date=end_dt,
            strategy=strategy,
            initial_capital=request.initial_capital,
            simulator=simulator
        )
        
        results = engine.run()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
