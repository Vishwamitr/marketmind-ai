from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
from data_pipeline.db_connector import DBConnector
from utils.config import Config
from api.auth_utils import get_current_active_user, User

router = APIRouter()

class OrderRequest(BaseModel):
    symbol: str
    action: str # 'BUY' or 'SELL'
    quantity: int

@router.get("/portfolio")
def get_portfolio(current_user: User = Depends(get_current_active_user)):
    try:
        with DBConnector.get_connection() as conn:
            # 1. Get Cash
            df_cash = pd.read_sql("SELECT * FROM portfolio_balance", conn)
            cash = df_cash.loc[df_cash['id'] == 1, 'cash'].iloc[0] if not df_cash.empty else 0.0

            # 2. Get Holdings
            df_holdings = pd.read_sql("SELECT symbol, quantity, avg_price FROM holdings", conn)
            holdings = df_holdings.to_dict(orient='records')

            # 3. Calculate Equity (Mark-to-Market)
            equity = cash
            total_holdings_value = 0.0
            
            # Enhaced holdings with current price
            enhanced_holdings = []
            for h in holdings:
                symbol = h['symbol']
                # Get latest price
                # Optimization: Could do a single query for all symbols if many, but loop is fine for MVP
                p_query = f"SELECT close FROM stock_prices WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT 1"
                df_p = pd.read_sql(p_query, conn)
                current_price = df_p.iloc[0]['close'] if not df_p.empty else h['avg_price']
                
                market_value = h['quantity'] * current_price
                unrealized_pnl = market_value - (h['quantity'] * h['avg_price'])
                
                enhanced_holdings.append({
                    **h,
                    "current_price": current_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "return_pct": (unrealized_pnl / (h['quantity'] * h['avg_price'])) * 100 if h['avg_price'] > 0 else 0
                })
                
                total_holdings_value += market_value

            equity += total_holdings_value

            return {
                "cash": cash,
                "equity": equity,
                "holdings_value": total_holdings_value,
                "holdings": enhanced_holdings
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order")
def place_order(order: OrderRequest, current_user: User = Depends(get_current_active_user)):
    try:
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Get Current Price
                cur.execute("SELECT close FROM stock_prices WHERE symbol = %s ORDER BY timestamp DESC LIMIT 1", (order.symbol,))
                res = cur.fetchone()
                if not res:
                    raise HTTPException(status_code=400, detail="Symbol not found or no price data")
                price = float(res[0])
                total_cost = price * order.quantity

                # 2. Get Cash
                cur.execute("SELECT cash FROM portfolio_balance WHERE id = 1 FOR UPDATE") # Lock row
                res_cash = cur.fetchone()
                current_cash = float(res_cash[0])

                if order.action == "BUY":
                    if current_cash < total_cost:
                        raise HTTPException(status_code=400, detail="Insufficient funds")
                    
                    # Update Cash
                    new_cash = current_cash - total_cost
                    cur.execute("UPDATE portfolio_balance SET cash = %s WHERE id = 1", (new_cash,))
                    
                    # Update Holdings
                    cur.execute("SELECT quantity, avg_price FROM holdings WHERE symbol = %s", (order.symbol,))
                    res_h = cur.fetchone()
                    
                    if res_h:
                        old_qty, old_avg = res_h
                        new_qty = old_qty + order.quantity
                        new_avg = ((old_qty * old_avg) + total_cost) / new_qty
                        cur.execute("UPDATE holdings SET quantity = %s, avg_price = %s WHERE symbol = %s", (new_qty, new_avg, order.symbol))
                    else:
                        cur.execute("INSERT INTO holdings (symbol, quantity, avg_price) VALUES (%s, %s, %s)", (order.symbol, order.quantity, price))

                elif order.action == "SELL":
                    # Check holdings
                    cur.execute("SELECT quantity, avg_price FROM holdings WHERE symbol = %s", (order.symbol,))
                    res_h = cur.fetchone()
                    if not res_h or res_h[0] < order.quantity:
                        raise HTTPException(status_code=400, detail="Insufficient holdings")
                    
                    old_qty, old_avg = res_h
                    
                    # Update Cash
                    new_cash = current_cash + total_cost
                    cur.execute("UPDATE portfolio_balance SET cash = %s WHERE id = 1", (new_cash,))
                    
                    # Update Holdings
                    new_qty = old_qty - order.quantity
                    if new_qty == 0:
                        cur.execute("DELETE FROM holdings WHERE symbol = %s", (order.symbol,))
                    else:
                        # Avg price doesn't change on sell
                        cur.execute("UPDATE holdings SET quantity = %s WHERE symbol = %s", (new_qty, order.symbol))

                # Log Transaction
                cur.execute(
                    "INSERT INTO transactions (symbol, action, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order.symbol, order.action, order.quantity, price)
                )

                conn.commit()
                
                return {"message": "Order executed", "price": price, "total": total_cost}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Portfolio Analytics ──────────────────────────────────────────────

SECTOR_MAP = {
    "RELIANCE": "Energy", "TCS": "IT", "HDFCBANK": "Banking", "INFY": "IT",
    "ICICIBANK": "Banking", "HINDUNILVR": "FMCG", "ITC": "FMCG",
    "BHARTIARTL": "Telecom", "SBIN": "Banking", "KOTAKBANK": "Banking",
    "LT": "Infra", "AXISBANK": "Banking", "BAJFINANCE": "Finance",
    "MARUTI": "Auto", "HCLTECH": "IT", "TITAN": "Consumer",
    "SUNPHARMA": "Pharma", "ASIANPAINT": "Consumer", "WIPRO": "IT",
    "TATAMOTORS": "Auto", "TATASTEEL": "Metals", "POWERGRID": "Power",
    "NTPC": "Power", "JSWSTEEL": "Metals", "TECHM": "IT",
    "DRREDDY": "Pharma", "NESTLEIND": "FMCG", "M&M": "Auto",
    "ADANIENT": "Infra", "BAJAJFINSV": "Finance",
}


@router.get("/portfolio/analytics")
def get_portfolio_analytics():
    """Compute portfolio risk metrics, sector allocation, and benchmark comparison."""
    try:
        import yfinance as yf
        import numpy as np

        with DBConnector.get_connection() as conn:
            df_holdings = pd.read_sql("SELECT symbol, quantity, avg_price FROM holdings", conn)

        if df_holdings.empty:
            return {"risk_metrics": {}, "allocation": [], "daily_returns": [], "benchmark_returns": []}

        holdings = df_holdings.to_dict(orient="records")
        portfolio_values = None
        total_invested = 0
        sector_allocation = {}

        for h in holdings:
            sym = h["symbol"]
            qty = h["quantity"]
            total_invested += qty * h["avg_price"]
            sector = SECTOR_MAP.get(sym, "Other")
            try:
                t = yf.Ticker(f"{sym}.NS")
                hist = t.history(period="6mo")
                if hist is None or hist.empty:
                    continue
                series = hist["Close"] * qty
                current_val = float(series.iloc[-1])
                sector_allocation[sector] = sector_allocation.get(sector, 0) + current_val
                if portfolio_values is None:
                    portfolio_values = series.copy()
                else:
                    portfolio_values = portfolio_values.add(series, fill_value=0)
            except Exception:
                continue

        if portfolio_values is None or len(portfolio_values) < 5:
            return {"risk_metrics": {}, "allocation": [], "daily_returns": [], "benchmark_returns": []}

        daily_returns = portfolio_values.pct_change().dropna()
        ann_return = float(daily_returns.mean() * 252)
        ann_vol = float(daily_returns.std() * np.sqrt(252))
        sharpe = round(ann_return / ann_vol, 2) if ann_vol > 0 else 0

        cummax = portfolio_values.cummax()
        drawdown = (portfolio_values - cummax) / cummax
        max_drawdown = round(float(drawdown.min()) * 100, 2)

        beta = 0
        benchmark_daily = []
        try:
            nifty = yf.Ticker("^NSEI")
            nifty_hist = nifty.history(period="6mo")
            if nifty_hist is not None and not nifty_hist.empty:
                nifty_ret = nifty_hist["Close"].pct_change().dropna()
                common = daily_returns.index.intersection(nifty_ret.index)
                if len(common) > 10:
                    p_ret = daily_returns.loc[common]
                    n_ret = nifty_ret.loc[common]
                    cov = float(np.cov(p_ret, n_ret)[0][1])
                    var_n = float(np.var(n_ret))
                    beta = round(cov / var_n, 2) if var_n > 0 else 0
                nifty_cum = ((1 + nifty_ret).cumprod() - 1) * 100
                for dt, val in nifty_cum.items():
                    benchmark_daily.append({"date": str(dt.date()), "return_pct": round(float(val), 2)})
        except Exception:
            pass

        port_cum = ((1 + daily_returns).cumprod() - 1) * 100
        port_daily = []
        for dt, val in port_cum.items():
            port_daily.append({"date": str(dt.date()), "return_pct": round(float(val), 2)})

        total_val = sum(sector_allocation.values())
        allocation = [
            {"sector": s, "value": round(v, 0), "pct": round((v / total_val) * 100, 1)}
            for s, v in sorted(sector_allocation.items(), key=lambda x: -x[1])
        ] if total_val > 0 else []

        return {
            "risk_metrics": {
                "sharpe_ratio": sharpe, "beta": beta, "max_drawdown": max_drawdown,
                "annualized_return": round(ann_return * 100, 2),
                "annualized_volatility": round(ann_vol * 100, 2),
                "best_day": round(float(daily_returns.max()) * 100, 2),
                "worst_day": round(float(daily_returns.min()) * 100, 2),
                "win_rate": round(float((daily_returns > 0).mean()) * 100, 1),
                "total_invested": round(total_invested, 0),
                "current_value": round(float(portfolio_values.iloc[-1]), 0),
            },
            "allocation": allocation,
            "daily_returns": port_daily[-60:],
            "benchmark_returns": benchmark_daily[-60:],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
