"""
Stock Predictions API — Time-series forecasting using historical data.
Uses linear regression + momentum as a lightweight prediction engine (free, no external API).
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import pandas as pd
import numpy as np
from data_pipeline.db_connector import DBConnector

router = APIRouter()
logger = logging.getLogger(__name__)


def _predict_prices(symbol: str, horizon: int = 7) -> dict:
    """
    Generate price predictions using a weighted moving average + momentum approach.
    Returns predicted prices for the next `horizon` trading days.
    """
    # Fetch historical data
    query = f"""
        SELECT timestamp, close, volume
        FROM stock_prices
        WHERE symbol = '{symbol}'
        ORDER BY timestamp DESC
        LIMIT 200
    """
    with DBConnector.get_connection() as conn:
        df = pd.read_sql(query, conn)

    if len(df) < 20:
        raise ValueError(f"Insufficient data for {symbol}. Need at least 20 data points, got {len(df)}.")

    df = df.sort_values("timestamp").reset_index(drop=True)
    closes = df["close"].values.astype(float)

    # Current price
    current_price = closes[-1]

    # Calculate momentum indicators
    # 1. Short-term momentum (5-day)
    if len(closes) >= 5:
        short_momentum = (closes[-1] - closes[-5]) / closes[-5]
    else:
        short_momentum = 0

    # 2. Medium-term momentum (20-day)
    if len(closes) >= 20:
        med_momentum = (closes[-1] - closes[-20]) / closes[-20]
    else:
        med_momentum = 0

    # 3. Linear regression slope (last 30 days)
    lookback = min(30, len(closes))
    recent = closes[-lookback:]
    x = np.arange(lookback)
    slope, intercept = np.polyfit(x, recent, 1)
    daily_trend = slope / current_price  # normalized daily trend

    # 4. Volatility (std of daily returns)
    returns = np.diff(closes[-30:]) / closes[-31:-1] if len(closes) >= 31 else np.diff(closes) / closes[:-1]
    volatility = np.std(returns) if len(returns) > 0 else 0.01

    # Weighted daily expected return
    daily_return = (
        0.4 * daily_trend +       # Linear regression trend
        0.3 * (short_momentum / 5) +  # Short momentum normalized per day
        0.2 * (med_momentum / 20) +   # Medium momentum normalized per day
        0.1 * 0                        # Placeholder for sentiment
    )

    # Cap daily return to avoid unrealistic predictions
    daily_return = max(-0.05, min(0.05, daily_return))

    # Generate predictions with slight randomness based on volatility
    np.random.seed(42)  # deterministic for same input
    predictions = []
    price = current_price

    for day in range(1, horizon + 1):
        # Add slight mean-reverting noise
        noise = np.random.normal(0, volatility * 0.3)
        price = price * (1 + daily_return + noise)
        predictions.append({
            "day": day,
            "predicted_price": round(float(price), 2),
            "change_pct": round(((price - current_price) / current_price) * 100, 2),
        })

    # Confidence based on data quality and volatility
    confidence = max(0.2, min(0.85, 0.7 - volatility * 5))

    # Direction
    final_price = predictions[-1]["predicted_price"]
    if final_price > current_price * 1.01:
        direction = "UP"
    elif final_price < current_price * 0.99:
        direction = "DOWN"
    else:
        direction = "FLAT"

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "horizon_days": horizon,
        "direction": direction,
        "confidence": round(confidence, 3),
        "predictions": predictions,
        "metadata": {
            "short_momentum_5d": round(short_momentum * 100, 2),
            "medium_momentum_20d": round(med_momentum * 100, 2),
            "daily_trend": round(daily_trend * 100, 4),
            "volatility": round(volatility * 100, 2),
            "data_points_used": len(closes),
        },
    }


@router.get("/predict/{symbol}")
def predict_stock(symbol: str, horizon: int = 7):
    """
    Predict stock price for the next N trading days.
    Uses momentum, linear regression, and volatility modeling.
    """
    symbol = symbol.strip().upper()
    if horizon < 1 or horizon > 30:
        raise HTTPException(status_code=400, detail="Horizon must be between 1 and 30 days")

    try:
        result = _predict_prices(symbol, horizon)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/batch/overview")
def predict_all_stocks(horizon: int = 7):
    """Predict prices for all tracked stocks."""
    try:
        query = "SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol"
        with DBConnector.get_connection() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return {"predictions": [], "count": 0}

        results = []
        for symbol in df["symbol"].tolist():
            try:
                pred = _predict_prices(symbol, horizon)
                results.append({
                    "symbol": pred["symbol"],
                    "current_price": pred["current_price"],
                    "direction": pred["direction"],
                    "confidence": pred["confidence"],
                    "predicted_final": pred["predictions"][-1]["predicted_price"],
                    "predicted_change_pct": pred["predictions"][-1]["change_pct"],
                })
            except Exception as e:
                logger.warning(f"Skipping prediction for {symbol}: {e}")

        results.sort(key=lambda r: r.get("predicted_change_pct", 0), reverse=True)
        return {"predictions": results, "count": len(results), "horizon_days": horizon}

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
