"""
Options API Router — with yfinance fallback, Black-Scholes Greeks, and Strategy Builder.
"""
import logging
import math
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Black-Scholes Greeks Calculator ──────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def _norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def _bs_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call") -> dict:
    """
    Calculate Black-Scholes Greeks.
    S = spot price, K = strike, T = time to expiry (years),
    r = risk-free rate, sigma = implied volatility (decimal, e.g. 0.25)
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T

    if option_type == "call":
        delta = round(_norm_cdf(d1), 4)
        theta = round((-(S * _norm_pdf(d1) * sigma) / (2 * sqrt_T) - r * K * math.exp(-r * T) * _norm_cdf(d2)) / 365, 4)
    else:
        delta = round(_norm_cdf(d1) - 1, 4)
        theta = round((-(S * _norm_pdf(d1) * sigma) / (2 * sqrt_T) + r * K * math.exp(-r * T) * _norm_cdf(-d2)) / 365, 4)

    gamma = round(_norm_pdf(d1) / (S * sigma * sqrt_T), 6)
    vega = round(S * _norm_pdf(d1) * sqrt_T / 100, 4)  # per 1% IV change

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}


def _fetch_live_options(symbol: str, expiry: Optional[str] = None):
    """Fetch live options chain from yfinance with Greeks."""
    import yfinance as yf
    from datetime import datetime

    ticker_sym = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    t = yf.Ticker(ticker_sym)

    # Get spot price
    try:
        fast = t.fast_info
        spot = float(fast.get("lastPrice", 0) or fast.get("regularMarketPrice", 0) or 0)
    except Exception:
        spot = 0

    if spot == 0:
        try:
            hist = t.history(period="1d")
            if hist is not None and not hist.empty:
                spot = float(hist["Close"].iloc[-1])
        except Exception:
            pass

    # Get available expiries
    try:
        expiries = list(t.options)
    except Exception:
        expiries = []

    if not expiries:
        return None

    # Use specified expiry or nearest
    target_expiry = expiry if expiry and expiry in expiries else expiries[0]
    r = 0.065  # RBI repo rate approx

    # Time to expiry in years
    try:
        exp_date = datetime.strptime(target_expiry, "%Y-%m-%d")
        T = max((exp_date - datetime.now()).days / 365.0, 1/365)
    except Exception:
        T = 30 / 365  # Default 30 days

    try:
        chain = t.option_chain(target_expiry)
    except Exception:
        return None

    def _process_option(row, option_type):
        strike = float(row.get("strike", 0))
        iv = float(row.get("impliedVolatility", 0))
        last = float(row.get("lastPrice", 0))
        bid = float(row.get("bid", 0))
        ask = float(row.get("ask", 0))
        vol = int(row.get("volume", 0)) if row.get("volume") and str(row.get("volume")) != "nan" else 0
        oi = int(row.get("openInterest", 0)) if row.get("openInterest") and str(row.get("openInterest")) != "nan" else 0
        itm = bool(row.get("inTheMoney", False))
        chg = round(float(row.get("percentChange", 0)), 2) if row.get("percentChange") and str(row.get("percentChange")) != "nan" else 0

        # Calculate Greeks
        greeks = _bs_greeks(spot, strike, T, r, iv, option_type) if spot > 0 and iv > 0 else {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

        return {
            "strike": strike,
            "last_price": last,
            "bid": bid,
            "ask": ask,
            "volume": vol,
            "open_interest": oi,
            "implied_volatility": round(iv * 100, 2),
            "in_the_money": itm,
            "change_pct": chg,
            "delta": greeks["delta"],
            "gamma": greeks["gamma"],
            "theta": greeks["theta"],
            "vega": greeks["vega"],
        }

    calls = [_process_option(row, "call") for _, row in chain.calls.iterrows()]
    puts = [_process_option(row, "put") for _, row in chain.puts.iterrows()]

    total_call_oi = sum(c["open_interest"] for c in calls)
    total_put_oi = sum(p["open_interest"] for p in puts)
    pcr = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else 0

    return {
        "symbol": symbol.upper(),
        "spot_price": round(spot, 2),
        "expiry": target_expiry,
        "available_expiries": expiries,
        "days_to_expiry": round(T * 365),
        "calls": calls,
        "puts": puts,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "put_call_ratio": pcr,
    }


@router.get("/options/chain/{symbol}")
def get_options_chain(symbol: str, expiry: Optional[str] = None):
    """
    Get options chain for a symbol.
    Returns calls and puts with strike, OI, IV, last price.
    """
    # Try DB first
    try:
        from data_pipeline.options_fetcher import OptionsFetcher
        fetcher = OptionsFetcher()
        chain = fetcher.get_chain(symbol.upper(), expiry=expiry)
        if chain["calls"] or chain["puts"]:
            return chain
    except Exception as e:
        logger.info(f"Options fetcher unavailable: {e}")

    # Fallback: yfinance
    try:
        result = _fetch_live_options(symbol.upper(), expiry)
        if result:
            return result
        raise HTTPException(status_code=404, detail=f"No options data for {symbol}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/expiries/{symbol}")
def get_available_expiries(symbol: str):
    """Get available expiry dates for a symbol."""
    try:
        from data_pipeline.options_fetcher import OptionsFetcher
        fetcher = OptionsFetcher()
        expiries = fetcher.get_expiries(symbol.upper())
        if expiries:
            return {"symbol": symbol.upper(), "expiries": expiries, "count": len(expiries)}
    except Exception as e:
        logger.info(f"Options DB unavailable: {e}")

    # yfinance fallback
    try:
        import yfinance as yf
        ticker_sym = f"{symbol.upper()}.NS"
        t = yf.Ticker(ticker_sym)
        expiries = list(t.options) if t.options else []
        return {"symbol": symbol.upper(), "expiries": expiries, "count": len(expiries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/overview")
def get_options_overview(limit: int = 20):
    """Get options overview — list of F&O stocks (instant, no yfinance calls)."""
    # Try DB first
    try:
        from data_pipeline.db_connector import DBConnector
        db = DBConnector()
        query = """
            WITH latest_fetch AS (
                SELECT symbol, MAX(fetched_at) as latest
                FROM options_chain
                GROUP BY symbol
            )
            SELECT
                oc.symbol,
                SUM(CASE WHEN oc.option_type = 'CALL' THEN oc.open_interest ELSE 0 END) as total_call_oi,
                SUM(CASE WHEN oc.option_type = 'PUT' THEN oc.open_interest ELSE 0 END) as total_put_oi,
                MAX(oc.implied_volatility) as max_iv,
                COUNT(*) as total_contracts,
                MIN(oc.expiry) as nearest_expiry
            FROM options_chain oc
            JOIN latest_fetch lf ON oc.symbol = lf.symbol AND oc.fetched_at = lf.latest
            GROUP BY oc.symbol
            ORDER BY total_call_oi + total_put_oi DESC
            LIMIT %s;
        """
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()

        if rows:
            results = []
            for r in rows:
                call_oi = r[1] or 0
                put_oi = r[2] or 0
                pcr = round(put_oi / call_oi, 3) if call_oi > 0 else 0
                results.append({
                    "symbol": r[0],
                    "total_call_oi": call_oi,
                    "total_put_oi": put_oi,
                    "put_call_ratio": pcr,
                    "max_iv_pct": round((r[3] or 0) * 100, 2),
                    "total_contracts": r[4],
                    "nearest_expiry": r[5].isoformat() if r[5] else None,
                    "sentiment": "Bearish" if pcr > 1.2 else "Bullish" if pcr < 0.8 else "Neutral",
                })
            return {"overview": results, "count": len(results)}
    except Exception as e:
        logger.info(f"Options DB unavailable: {e}")

    # Fallback: return static list of popular F&O stocks (INSTANT — no yfinance)
    # Users click on a symbol to load its live chain on-demand
    FNO_LIST = [
        {"symbol": "NIFTY", "name": "NIFTY 50 Index", "lot_size": 25},
        {"symbol": "BANKNIFTY", "name": "Bank NIFTY Index", "lot_size": 15},
        {"symbol": "FINNIFTY", "name": "FIN NIFTY Index", "lot_size": 25},
        {"symbol": "RELIANCE", "name": "Reliance Industries", "lot_size": 250},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "lot_size": 150},
        {"symbol": "HDFCBANK", "name": "HDFC Bank", "lot_size": 550},
        {"symbol": "INFY", "name": "Infosys", "lot_size": 300},
        {"symbol": "ICICIBANK", "name": "ICICI Bank", "lot_size": 700},
        {"symbol": "SBIN", "name": "State Bank of India", "lot_size": 750},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "lot_size": 475},
        {"symbol": "ITC", "name": "ITC Limited", "lot_size": 1600},
        {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "lot_size": 400},
        {"symbol": "LT", "name": "Larsen & Toubro", "lot_size": 150},
        {"symbol": "AXISBANK", "name": "Axis Bank", "lot_size": 600},
        {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "lot_size": 125},
        {"symbol": "MARUTI", "name": "Maruti Suzuki", "lot_size": 100},
        {"symbol": "TITAN", "name": "Titan Company", "lot_size": 375},
        {"symbol": "TATAMOTORS", "name": "Tata Motors", "lot_size": 550},
        {"symbol": "TATASTEEL", "name": "Tata Steel", "lot_size": 550},
        {"symbol": "WIPRO", "name": "Wipro", "lot_size": 1500},
    ]

    results = []
    for fno in FNO_LIST[:limit]:
        results.append({
            "symbol": fno["symbol"],
            "name": fno["name"],
            "lot_size": fno["lot_size"],
            "total_call_oi": 0,
            "total_put_oi": 0,
            "put_call_ratio": 0,
            "max_iv_pct": 0,
            "total_contracts": 0,
            "nearest_expiry": None,
            "sentiment": "Click to load",
        })

    return {"overview": results, "count": len(results), "static": True}


@router.get("/options/max-pain/{symbol}")
def get_max_pain(symbol: str, expiry: Optional[str] = None):
    """Calculate max pain for a symbol at a given expiry."""
    # Get options chain (will use fallback automatically)
    try:
        chain = None
        try:
            from data_pipeline.options_fetcher import OptionsFetcher
            fetcher = OptionsFetcher()
            chain = fetcher.get_chain(symbol.upper(), expiry=expiry)
        except Exception:
            pass

        if not chain or (not chain.get("calls") and not chain.get("puts")):
            chain = _fetch_live_options(symbol.upper(), expiry)

        if not chain or not chain.get("calls") or not chain.get("puts"):
            raise HTTPException(status_code=404, detail="No options data")

        calls = chain["calls"]
        puts = chain["puts"]

        strikes = sorted(set(c["strike"] for c in calls))
        min_pain = float("inf")
        max_pain_strike = 0

        for strike in strikes:
            call_pain = sum(
                max(0, strike - c["strike"]) * c["open_interest"]
                for c in calls
            )
            put_pain = sum(
                max(0, p["strike"] - strike) * p["open_interest"]
                for p in puts
            )
            total_pain = call_pain + put_pain
            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = strike

        return {
            "symbol": symbol.upper(),
            "max_pain": max_pain_strike,
            "put_call_ratio": chain.get("put_call_ratio", 0),
            "total_call_oi": chain.get("total_call_oi", 0),
            "total_put_oi": chain.get("total_put_oi", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Strategy Builder ─────────────────────────────────────────────────

class StrategyLeg(BaseModel):
    option_type: str   # "call" or "put"
    strike: float
    premium: float
    quantity: int      # positive = buy, negative = sell
    lot_size: int = 1

class StrategyRequest(BaseModel):
    legs: List[StrategyLeg]
    spot_price: float = 0
    price_range_pct: float = 20  # % range around center

@router.post("/options/strategy/payoff")
def calculate_strategy_payoff(req: StrategyRequest):
    """Calculate P&L payoff diagram for a multi-leg options strategy."""
    if not req.legs:
        raise HTTPException(status_code=400, detail="At least one leg is required")

    strikes = [leg.strike for leg in req.legs]
    center = req.spot_price if req.spot_price > 0 else sum(strikes) / len(strikes)
    range_val = center * (req.price_range_pct / 100)
    start = max(0, center - range_val)
    end = center + range_val
    step = (end - start) / 200  # 200 data points

    payoff = []
    price = start
    while price <= end:
        total_pnl = 0
        for leg in req.legs:
            if leg.option_type == "call":
                intrinsic = max(0, price - leg.strike)
            else:
                intrinsic = max(0, leg.strike - price)
            pnl = (intrinsic - leg.premium) * leg.quantity * leg.lot_size
            total_pnl += pnl
        payoff.append({
            "price": round(price, 2),
            "pnl": round(total_pnl, 2),
        })
        price += step

    # Find breakeven points
    breakevens = []
    for i in range(1, len(payoff)):
        if (payoff[i-1]["pnl"] < 0 and payoff[i]["pnl"] >= 0) or \
           (payoff[i-1]["pnl"] >= 0 and payoff[i]["pnl"] < 0):
            breakevens.append(payoff[i]["price"])

    max_profit = max(p["pnl"] for p in payoff)
    max_loss = min(p["pnl"] for p in payoff)

    return {
        "payoff": payoff,
        "breakevens": breakevens,
        "max_profit": round(max_profit, 2),
        "max_loss": round(max_loss, 2),
        "center_price": round(center, 2),
    }


@router.get("/options/strategies/templates")
def get_strategy_templates():
    """Get pre-built options strategy templates."""
    return {
        "templates": [
            {
                "name": "Bull Call Spread",
                "description": "Buy lower strike call, sell higher strike call. Limited risk, limited reward.",
                "sentiment": "Moderately Bullish",
                "legs": [
                    {"option_type": "call", "strike_offset": -2, "quantity": 1},
                    {"option_type": "call", "strike_offset": 2, "quantity": -1},
                ],
            },
            {
                "name": "Bear Put Spread",
                "description": "Buy higher strike put, sell lower strike put. Limited risk, limited reward.",
                "sentiment": "Moderately Bearish",
                "legs": [
                    {"option_type": "put", "strike_offset": 2, "quantity": 1},
                    {"option_type": "put", "strike_offset": -2, "quantity": -1},
                ],
            },
            {
                "name": "Long Straddle",
                "description": "Buy ATM call and put. Profit from big moves in either direction.",
                "sentiment": "High Volatility Expected",
                "legs": [
                    {"option_type": "call", "strike_offset": 0, "quantity": 1},
                    {"option_type": "put", "strike_offset": 0, "quantity": 1},
                ],
            },
            {
                "name": "Iron Condor",
                "description": "Sell OTM call and put spreads. Profit from low volatility.",
                "sentiment": "Neutral / Low Volatility",
                "legs": [
                    {"option_type": "put", "strike_offset": -4, "quantity": 1},
                    {"option_type": "put", "strike_offset": -2, "quantity": -1},
                    {"option_type": "call", "strike_offset": 2, "quantity": -1},
                    {"option_type": "call", "strike_offset": 4, "quantity": 1},
                ],
            },
            {
                "name": "Protective Put",
                "description": "Hold stock + buy put for downside protection.",
                "sentiment": "Bullish with Protection",
                "legs": [
                    {"option_type": "put", "strike_offset": -2, "quantity": 1},
                ],
            },
            {
                "name": "Covered Call",
                "description": "Hold stock + sell OTM call for income.",
                "sentiment": "Mildly Bullish",
                "legs": [
                    {"option_type": "call", "strike_offset": 2, "quantity": -1},
                ],
            },
        ]
    }


# ── IV Smile / Skew ─────────────────────────────────────────────────

@router.get("/options/iv-smile/{symbol}")
def get_iv_smile(symbol: str, expiry: Optional[str] = None):
    """Get IV vs Strike data for smile/skew visualization."""
    try:
        import yfinance as yf
        ticker_sym = f"{symbol.strip().upper()}.NS"
        t = yf.Ticker(ticker_sym)

        exps = t.options
        if not exps:
            raise HTTPException(status_code=404, detail="No options expiries found")

        selected_expiry = expiry if expiry and expiry in exps else exps[0]
        chain = t.option_chain(selected_expiry)

        # Get spot price
        hist = t.history(period="1d")
        spot = float(hist["Close"].iloc[-1]) if hist is not None and not hist.empty else 0

        calls_data = []
        puts_data = []

        for _, row in chain.calls.iterrows():
            iv = row.get("impliedVolatility", 0)
            strike = float(row.get("strike", 0))
            if iv and iv > 0 and strike > 0:
                calls_data.append({
                    "strike": strike,
                    "iv": round(float(iv) * 100, 2),
                    "oi": int(row.get("openInterest", 0) or 0),
                    "volume": int(row.get("volume", 0) or 0),
                })

        for _, row in chain.puts.iterrows():
            iv = row.get("impliedVolatility", 0)
            strike = float(row.get("strike", 0))
            if iv and iv > 0 and strike > 0:
                puts_data.append({
                    "strike": strike,
                    "iv": round(float(iv) * 100, 2),
                    "oi": int(row.get("openInterest", 0) or 0),
                    "volume": int(row.get("volume", 0) or 0),
                })

        # ATM strike (closest to spot)
        all_strikes = [c["strike"] for c in calls_data]
        atm_strike = min(all_strikes, key=lambda s: abs(s - spot)) if all_strikes and spot else 0
        atm_iv = next((c["iv"] for c in calls_data if c["strike"] == atm_strike), 0)

        # Skew metric: difference between OTM put IV and OTM call IV
        otm_put_iv = [p["iv"] for p in puts_data if p["strike"] < atm_strike]
        otm_call_iv = [c["iv"] for c in calls_data if c["strike"] > atm_strike]

        skew = round(
            (sum(otm_put_iv) / len(otm_put_iv) if otm_put_iv else 0) -
            (sum(otm_call_iv) / len(otm_call_iv) if otm_call_iv else 0),
            2
        )

        return {
            "symbol": symbol.upper(),
            "expiry": selected_expiry,
            "spot_price": round(spot, 2),
            "atm_strike": atm_strike,
            "atm_iv": atm_iv,
            "skew": skew,
            "calls": sorted(calls_data, key=lambda x: x["strike"]),
            "puts": sorted(puts_data, key=lambda x: x["strike"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IV smile failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
