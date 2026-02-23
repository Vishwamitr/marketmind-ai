"""
Mutual Funds API Router — uses AMFI API for fast, comprehensive Indian MF data.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import requests

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache for AMFI NAV data (refreshed per request, very fast)
_amfi_cache = {"data": [], "ts": None}


def _fetch_amfi_navs(force_refresh: bool = False):
    """
    Fetch all MF NAVs from AMFI India API (free, no auth, ~3000 funds).
    This is a single HTTP call that returns ALL fund NAVs — very fast.
    """
    import pandas as pd
    from datetime import datetime, timedelta

    # Use cache if less than 5 minutes old
    if (
        not force_refresh
        and _amfi_cache["data"]
        and _amfi_cache["ts"]
        and (datetime.now() - _amfi_cache["ts"]) < timedelta(minutes=5)
    ):
        return _amfi_cache["data"]

    try:
        url = "https://www.amfiindia.com/spages/NAVAll.txt"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        funds = []
        current_category = "Other"

        for line in lines:
            line = line.strip()
            if not line or line.startswith("Scheme Code"):
                continue

            parts = line.split(";")

            # Category header lines (no semicolons, or different format)
            if len(parts) < 4:
                # This is a category line
                current_category = line.strip()
                continue

            try:
                scheme_code = parts[0].strip()
                # ISIN fields are parts[1] and parts[2]
                scheme_name = parts[3].strip()
                nav_str = parts[4].strip()
                date_str = parts[5].strip() if len(parts) > 5 else ""

                # Skip if NAV is not a number
                if nav_str in ("N/A", "-", ""):
                    continue

                nav = float(nav_str)

                funds.append({
                    "symbol": scheme_code,
                    "fund_name": scheme_name,
                    "nav": round(nav, 4),
                    "category": _simplify_category(current_category),
                    "raw_category": current_category,
                    "timestamp": date_str or str(pd.Timestamp.now().date()),
                })
            except (ValueError, IndexError):
                continue

        _amfi_cache["data"] = funds
        _amfi_cache["ts"] = datetime.now()

        return funds

    except Exception as e:
        logger.error(f"AMFI API error: {e}")
        # Fall back to cached data if available
        if _amfi_cache["data"]:
            return _amfi_cache["data"]
        raise


def _simplify_category(raw: str) -> str:
    """Simplify AMFI category names for display."""
    raw_lower = raw.lower()
    if "equity" in raw_lower and "large" in raw_lower:
        return "Large Cap"
    if "equity" in raw_lower and "mid" in raw_lower:
        return "Mid Cap"
    if "equity" in raw_lower and "small" in raw_lower:
        return "Small Cap"
    if "equity" in raw_lower and "flexi" in raw_lower:
        return "Flexi Cap"
    if "equity" in raw_lower and "multi" in raw_lower:
        return "Multi Cap"
    if "index" in raw_lower or "nifty" in raw_lower or "sensex" in raw_lower:
        return "Index Fund"
    if "debt" in raw_lower or "bond" in raw_lower or "gilt" in raw_lower:
        return "Debt"
    if "liquid" in raw_lower or "money market" in raw_lower:
        return "Liquid"
    if "hybrid" in raw_lower or "balanced" in raw_lower:
        return "Hybrid"
    if "elss" in raw_lower or "tax" in raw_lower:
        return "ELSS"
    if "sectoral" in raw_lower or "thematic" in raw_lower:
        return "Sectoral"
    if "international" in raw_lower or "global" in raw_lower:
        return "International"
    if "gold" in raw_lower:
        return "Gold"
    if "equity" in raw_lower:
        return "Equity"
    return "Other"


@router.get("/mf/list")
def get_mf_list(category: Optional[str] = None, limit: int = 100, search: Optional[str] = None):
    """Get mutual funds with latest NAV. Uses AMFI API (~3000 funds, instant)."""
    # Try DB first
    try:
        from data_pipeline.mf_fetcher import MFNavFetcher
        fetcher = MFNavFetcher()
        navs = fetcher.get_latest_navs()
        if navs:
            if search:
                s = search.lower()
                navs = [n for n in navs if s in n["fund_name"].lower() or s in n["symbol"].lower()]
            if category:
                navs = [n for n in navs if n["category"].lower() == category.lower()]
            navs = navs[:limit]
            return {
                "funds": navs,
                "count": len(navs),
                "categories": list(set(n["category"] for n in navs)),
            }
    except Exception as e:
        logger.info(f"MF fetcher unavailable: {e}")

    # Fallback: AMFI API
    try:
        funds = _fetch_amfi_navs()

        if search:
            s = search.lower()
            funds = [f for f in funds if s in f["fund_name"].lower() or s in f["symbol"].lower()]

        if category:
            funds = [f for f in funds if f["category"].lower() == category.lower()]

        # Get all categories before limiting
        all_categories = sorted(set(f["category"] for f in funds)) if funds else []
        funds = funds[:limit]

        return {
            "funds": funds,
            "count": len(funds),
            "categories": all_categories,
            "total_available": len(_amfi_cache["data"]) if _amfi_cache["data"] else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mf/search")
def search_mf(q: str = Query("", min_length=1, max_length=100), limit: int = 15):
    """Search mutual funds by name or scheme code."""
    try:
        funds = _fetch_amfi_navs()
        q_lower = q.lower()
        results = [
            {"symbol": f["symbol"], "fund_name": f["fund_name"], "nav": f["nav"], "category": f["category"]}
            for f in funds
            if q_lower in f["fund_name"].lower() or q_lower in f["symbol"]
        ][:limit]
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mf/history/{symbol}")
def get_mf_history(symbol: str, limit: int = 365):
    """Get NAV history for a specific mutual fund using mfapi.in (free, historical data)."""
    # Try DB first
    try:
        from data_pipeline.mf_fetcher import MFNavFetcher
        fetcher = MFNavFetcher()
        history = fetcher.get_nav_history(symbol, limit=limit)
        if history:
            latest_nav = history[-1]["nav"]
            first_nav = history[0]["nav"]
            total_return = ((latest_nav - first_nav) / first_nav) * 100 if len(history) >= 2 else 0
            return {
                "symbol": symbol,
                "history": history,
                "count": len(history),
                "latest_nav": latest_nav,
                "total_return_pct": round(total_return, 2),
            }
    except Exception as e:
        logger.info(f"MF history DB unavailable: {e}")

    # Primary fallback: mfapi.in — free historical NAV API for Indian MFs
    # Works with AMFI scheme codes (numeric), provides full history
    if symbol.isdigit():
        try:
            mf_url = f"https://api.mfapi.in/mf/{symbol}"
            resp = requests.get(mf_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("data"):
                nav_data = data["data"]  # list of {"date": "DD-MM-YYYY", "nav": "123.45"}
                history = []
                for entry in reversed(nav_data[:limit]):  # reversed so oldest first
                    try:
                        nav_val = float(entry["nav"])
                        history.append({
                            "timestamp": entry["date"],
                            "nav": round(nav_val, 4),
                        })
                    except (ValueError, KeyError):
                        continue

                if history:
                    fund_name = data.get("meta", {}).get("fund_house", "") + " - " + data.get("meta", {}).get("scheme_name", symbol)
                    latest_nav = history[-1]["nav"]
                    first_nav = history[0]["nav"]
                    total_return = ((latest_nav - first_nav) / first_nav) * 100 if first_nav > 0 else 0

                    return {
                        "symbol": symbol,
                        "fund_name": fund_name.strip(" - "),
                        "history": history,
                        "count": len(history),
                        "latest_nav": latest_nav,
                        "total_return_pct": round(total_return, 2),
                    }
        except Exception as e:
            logger.warning(f"mfapi.in failed for {symbol}: {e}")

    # Secondary fallback: yfinance for ETFs (non-numeric symbols)
    if not symbol.isdigit():
        try:
            import yfinance as yf
            ticker_sym = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
            t = yf.Ticker(ticker_sym)
            hist = t.history(period="1y")

            if not hist.empty:
                history = []
                for date, row in hist.iterrows():
                    history.append({
                        "timestamp": str(date),
                        "nav": round(float(row["Close"]), 2),
                    })

                latest_nav = history[-1]["nav"]
                first_nav = history[0]["nav"]
                total_return = ((latest_nav - first_nav) / first_nav) * 100

                return {
                    "symbol": symbol,
                    "history": history[-limit:],
                    "count": len(history),
                    "latest_nav": latest_nav,
                    "total_return_pct": round(total_return, 2),
                }
        except Exception:
            pass

    # Last resort: current NAV from AMFI
    try:
        funds = _fetch_amfi_navs()
        fund = next((f for f in funds if f["symbol"] == symbol), None)
        if fund:
            return {
                "symbol": symbol,
                "fund_name": fund["fund_name"],
                "history": [{"timestamp": fund["timestamp"], "nav": fund["nav"]}],
                "count": 1,
                "latest_nav": fund["nav"],
                "total_return_pct": 0,
                "note": "Historical data not available for this fund. Showing latest NAV only.",
            }
    except Exception:
        pass

    raise HTTPException(status_code=404, detail=f"No data for {symbol}")


@router.get("/mf/top-performers")
def get_top_performers(category: Optional[str] = None, period_days: int = 30, limit: int = 20):
    """Get top performing mutual funds."""
    try:
        from data_pipeline.db_connector import DBConnector
        db = DBConnector()
        query = """
            WITH latest AS (
                SELECT DISTINCT ON (symbol) symbol, fund_name, nav AS latest_nav, category, timestamp
                FROM mutual_fund_nav
                ORDER BY symbol, timestamp DESC
            ),
            past AS (
                SELECT DISTINCT ON (symbol) symbol, nav AS past_nav
                FROM mutual_fund_nav
                WHERE timestamp <= NOW() - INTERVAL '%s days'
                ORDER BY symbol, timestamp DESC
            )
            SELECT l.symbol, l.fund_name, l.latest_nav, l.category,
                   l.timestamp, p.past_nav,
                   ((l.latest_nav - p.past_nav) / p.past_nav * 100) AS return_pct
            FROM latest l
            JOIN past p ON l.symbol = p.symbol
            WHERE p.past_nav > 0
            ORDER BY return_pct DESC
            LIMIT %s;
        """
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (period_days, limit))
                rows = cur.fetchall()

        if rows:
            results = []
            for r in rows:
                entry = {
                    "symbol": r[0], "fund_name": r[1], "latest_nav": r[2],
                    "category": r[3], "timestamp": r[4].isoformat(),
                    "past_nav": r[5], "return_pct": round(r[6], 2),
                }
                if category and entry["category"].lower() != category.lower():
                    continue
                results.append(entry)
            return {"top_performers": results, "period_days": period_days, "count": len(results)}
    except Exception as e:
        logger.info(f"MF top performers DB unavailable: {e}")

    # Fallback: show highest NAV funds from AMFI
    try:
        funds = _fetch_amfi_navs()
        if category:
            funds = [f for f in funds if f["category"].lower() == category.lower()]

        # Sort by NAV as proxy (not ideal but best we can do without history)
        funds.sort(key=lambda x: x.get("nav", 0), reverse=True)
        results = [{
            "symbol": f["symbol"], "fund_name": f["fund_name"],
            "latest_nav": f["nav"], "category": f["category"],
            "return_pct": 0,
        } for f in funds[:limit]]

        return {"top_performers": results, "period_days": period_days, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mf/categories")
def get_mf_categories():
    """Get available mutual fund categories."""
    try:
        funds = _fetch_amfi_navs()
        categories = sorted(set(f["category"] for f in funds))
        return {"categories": categories}
    except Exception:
        return {"categories": [
            "Large Cap", "Mid Cap", "Small Cap", "Flexi Cap", "Multi Cap",
            "Index Fund", "Debt", "Liquid", "Hybrid", "ELSS", "Sectoral",
            "International", "Gold", "Equity", "Other",
        ]}
