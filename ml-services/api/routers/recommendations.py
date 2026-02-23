"""
AI Recommendations API — Combines regime + technicals + sentiment into actionable signals.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import logging
import pandas as pd
from data_pipeline.db_connector import DBConnector
from analysis.regime_detector import RegimeDetector

router = APIRouter()
logger = logging.getLogger(__name__)
regime_detector = RegimeDetector()


def _generate_recommendation(symbol: str) -> Dict:
    """
    Generate a BUY/HOLD/SELL recommendation for a single stock
    by combining regime detection, technicals, and price momentum.
    """
    signals = []
    score = 0.0  # -1 (strong sell) to +1 (strong buy)
    confidence = 0.5

    # --- 1. Regime Detection ---
    try:
        regime, metrics = regime_detector.detect_regime(symbol)
        regime_val = regime.value.lower()

        if "bull" in regime_val:
            signals.append({"type": "regime", "signal": "bullish", "detail": "Market regime is bullish"})
            score += 0.3
        elif "bear" in regime_val:
            signals.append({"type": "regime", "signal": "bearish", "detail": "Market regime is bearish"})
            score -= 0.3
        elif "sideways" in regime_val:
            signals.append({"type": "regime", "signal": "neutral", "detail": "Market is range-bound"})
        elif "volatile" in regime_val:
            signals.append({"type": "regime", "signal": "caution", "detail": "High volatility detected"})
            score -= 0.1

        # ADX — trend strength
        adx = metrics.get("adx")
        if adx:
            if adx > 25:
                signals.append({"type": "technical", "signal": "strong_trend", "detail": f"ADX={adx:.1f} — strong trend"})
                confidence += 0.1
            else:
                signals.append({"type": "technical", "signal": "weak_trend", "detail": f"ADX={adx:.1f} — weak/no trend"})
                confidence -= 0.05

        # Price vs SMA 200
        sma_200 = metrics.get("sma_200")
        close = metrics.get("close")
        if sma_200 and close:
            if close > sma_200:
                signals.append({"type": "technical", "signal": "above_sma200", "detail": f"Price above SMA200 (₹{sma_200:.2f})"})
                score += 0.15
            else:
                signals.append({"type": "technical", "signal": "below_sma200", "detail": f"Price below SMA200 (₹{sma_200:.2f})"})
                score -= 0.15

        # ATR for risk context
        atr = metrics.get("atr")
        if atr and close:
            atr_pct = (atr / close) * 100
            if atr_pct > 3:
                signals.append({"type": "risk", "signal": "high_volatility", "detail": f"ATR={atr:.2f} ({atr_pct:.1f}% of price)"})
            else:
                signals.append({"type": "risk", "signal": "normal_volatility", "detail": f"ATR={atr:.2f} ({atr_pct:.1f}% of price)"})

    except Exception as e:
        logger.warning(f"Regime detection failed for {symbol}: {e}")
        signals.append({"type": "error", "signal": "regime_unavailable", "detail": str(e)})

    # --- 2. Price Momentum (from DB) ---
    try:
        query = f"""
            SELECT close, volume
            FROM stock_prices
            WHERE symbol = '{symbol}'
            ORDER BY timestamp DESC
            LIMIT 10
        """
        with DBConnector.get_connection() as conn:
            df = pd.read_sql(query, conn)

        if len(df) >= 5:
            # 5-day return
            current = df["close"].iloc[0]
            five_ago = df["close"].iloc[4]
            five_day_return = ((current - five_ago) / five_ago) * 100

            if five_day_return > 3:
                signals.append({"type": "momentum", "signal": "strong_positive", "detail": f"5-day return: +{five_day_return:.1f}%"})
                score += 0.15
            elif five_day_return < -3:
                signals.append({"type": "momentum", "signal": "strong_negative", "detail": f"5-day return: {five_day_return:.1f}%"})
                score -= 0.15
            else:
                signals.append({"type": "momentum", "signal": "flat", "detail": f"5-day return: {five_day_return:+.1f}%"})

            # Volume trend
            avg_vol = df["volume"].mean()
            latest_vol = df["volume"].iloc[0]
            if latest_vol > avg_vol * 1.5:
                signals.append({"type": "volume", "signal": "high_volume", "detail": f"Volume {latest_vol/avg_vol:.1f}x average"})
                confidence += 0.05

    except Exception as e:
        logger.warning(f"Momentum analysis failed for {symbol}: {e}")

    # --- 3. Sentiment (from MongoDB) ---
    try:
        from data_pipeline.mongo_connector import MongoConnector
        db = MongoConnector.get_db()
        pipeline = [
            {"$match": {
                "$or": [
                    {"title": {"$regex": symbol, "$options": "i"}},
                    {"summary": {"$regex": symbol, "$options": "i"}}
                ],
                "sentiment": {"$exists": True}
            }},
            {"$sort": {"published_at": -1}},
            {"$limit": 10},
            {"$group": {
                "_id": None,
                "avg_score": {"$avg": "$sentiment.score"},
                "count": {"$sum": 1},
                "positive": {"$sum": {"$cond": [{"$eq": ["$sentiment.label", "positive"]}, 1, 0]}},
                "negative": {"$sum": {"$cond": [{"$eq": ["$sentiment.label", "negative"]}, 1, 0]}},
            }}
        ]
        result = list(db.news_articles.aggregate(pipeline))
        if result:
            sentiment = result[0]
            if sentiment["positive"] > sentiment["negative"]:
                signals.append({"type": "sentiment", "signal": "positive", "detail": f"Sentiment: {sentiment['positive']}/{sentiment['count']} positive articles"})
                score += 0.1
            elif sentiment["negative"] > sentiment["positive"]:
                signals.append({"type": "sentiment", "signal": "negative", "detail": f"Sentiment: {sentiment['negative']}/{sentiment['count']} negative articles"})
                score -= 0.1
            else:
                signals.append({"type": "sentiment", "signal": "neutral", "detail": f"Sentiment: mixed ({sentiment['count']} articles)"})
    except Exception as e:
        logger.debug(f"Sentiment analysis failed for {symbol}: {e}")

    # --- Final recommendation ---
    confidence = max(0.1, min(0.95, confidence))
    score = max(-1.0, min(1.0, score))

    if score > 0.2:
        action = "BUY"
    elif score < -0.2:
        action = "SELL"
    else:
        action = "HOLD"

    # --- Calculate Entry / Target / Stop Loss ---
    entry = None
    target = None
    stop_loss = None
    risk_reward = None

    try:
        # Get live price and ATR for level calculation
        import yfinance as yf
        t = yf.Ticker(f"{symbol}.NS")
        hist = t.history(period="20d")
        if hist is not None and not hist.empty:
            current_price = float(hist["Close"].iloc[-1])
            entry = round(current_price, 2)

            # ATR-based levels
            tr = hist["High"] - hist["Low"]
            atr_val = float(tr.rolling(14).mean().iloc[-1]) if len(hist) >= 14 else float(tr.mean())

            if action == "BUY":
                target = round(entry + 2.0 * atr_val, 2)
                stop_loss = round(entry - 1.5 * atr_val, 2)
            elif action == "SELL":
                target = round(entry - 2.0 * atr_val, 2)
                stop_loss = round(entry + 1.5 * atr_val, 2)
            else:  # HOLD
                target = round(entry + 1.0 * atr_val, 2)
                stop_loss = round(entry - 1.0 * atr_val, 2)

            # Risk:Reward
            if stop_loss and target and entry:
                risk = abs(entry - stop_loss)
                reward = abs(target - entry)
                risk_reward = round(reward / risk, 2) if risk > 0 else 0
    except Exception as e:
        logger.debug(f"Price level calculation failed for {symbol}: {e}")

    return {
        "symbol": symbol,
        "action": action,
        "score": round(score, 3),
        "confidence": round(confidence, 3),
        "confidence_pct": round(confidence * 100, 1),
        "entry": entry,
        "target": target,
        "stop_loss": stop_loss,
        "risk_reward": risk_reward,
        "signals": signals,
        "signal_count": len(signals),
    }


@router.get("/recommend/{symbol}")
def get_recommendation(symbol: str):
    """Get AI recommendation for a single stock."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol required")

    try:
        rec = _generate_recommendation(symbol)
        return rec
    except Exception as e:
        logger.error(f"Recommendation failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend/all/overview")
def get_all_recommendations():
    """Get AI recommendations for all tracked stocks."""
    # Symbols to exclude from recommendations (test/internal entries)
    EXCLUDED_SYMBOLS = {'MONITOR_TEST', 'TEST', 'DEMO'}

    try:
        query = """
            SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol
        """
        with DBConnector.get_connection() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            return {"recommendations": [], "count": 0}

        recommendations = []
        for symbol in df["symbol"].tolist():
            # Skip test/internal symbols
            if symbol in EXCLUDED_SYMBOLS or 'MONITOR' in symbol.upper() or 'TEST' in symbol.upper():
                continue
            try:
                rec = _generate_recommendation(symbol)
                recommendations.append(rec)
            except Exception as e:
                logger.warning(f"Skipping {symbol}: {e}")
                recommendations.append({
                    "symbol": symbol, "action": "UNKNOWN", "score": 0,
                    "confidence": 0, "signals": [], "signal_count": 0,
                    "error": str(e),
                })

        # Sort by score descending (best buys first)
        recommendations.sort(key=lambda r: r["score"], reverse=True)

        return {"recommendations": recommendations, "count": len(recommendations)}

    except Exception as e:
        logger.error(f"All recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
