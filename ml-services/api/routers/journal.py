"""
Trade Journal API Router — SQLite-backed trade log with P&L stats.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'journal.db')


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT    NOT NULL,
            direction   TEXT    NOT NULL DEFAULT 'LONG',
            entry_price REAL    NOT NULL,
            exit_price  REAL    NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            trade_date  TEXT    NOT NULL,
            strategy    TEXT,
            notes       TEXT,
            created_at  TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn


class TradeIn(BaseModel):
    symbol: str
    direction: str = "LONG"  # LONG / SHORT
    entry_price: float
    exit_price: float
    quantity: int = 1
    trade_date: str = ""
    strategy: Optional[str] = None
    notes: Optional[str] = None


@router.get("/journal")
async def list_trades():
    try:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM trades ORDER BY trade_date DESC, created_at DESC").fetchall()
        trades = []
        for r in rows:
            t = dict(r)
            # Calculate P&L per share and total
            direction = t.get("direction", "LONG").upper()
            entry = t.get("entry_price", 0)
            exit_ = t.get("exit_price", 0)
            qty = t.get("quantity", 1)
            pnl_per = (exit_ - entry) if direction == "LONG" else (entry - exit_)
            t["pnl_per_share"] = round(pnl_per, 2)
            t["total_pnl"] = round(pnl_per * qty, 2)
            t["pnl_pct"] = round((pnl_per / entry) * 100, 2) if entry else 0
            trades.append(t)
        conn.close()
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Journal list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/journal")
async def add_trade(trade: TradeIn):
    try:
        conn = _get_db()
        date_str = trade.trade_date or datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO trades (symbol, direction, entry_price, exit_price, quantity, trade_date, strategy, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (trade.symbol.upper(), trade.direction.upper(), trade.entry_price, trade.exit_price,
             trade.quantity, date_str, trade.strategy, trade.notes, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "message": "Trade logged"}
    except Exception as e:
        logger.error(f"Journal add failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/journal/{trade_id}")
async def delete_trade(trade_id: int):
    try:
        conn = _get_db()
        conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/journal/stats")
async def get_journal_stats():
    try:
        conn = _get_db()
        rows = conn.execute("SELECT * FROM trades").fetchall()
        conn.close()

        if not rows:
            return {"total_trades": 0, "win_rate": 0, "total_pnl": 0, "avg_pnl": 0, "best_trade": None, "worst_trade": None}

        pnls = []
        for r in rows:
            t = dict(r)
            direction = t.get("direction", "LONG").upper()
            entry = t.get("entry_price", 0)
            exit_ = t.get("exit_price", 0)
            qty = t.get("quantity", 1)
            pnl = ((exit_ - entry) if direction == "LONG" else (entry - exit_)) * qty
            pnls.append({"symbol": t["symbol"], "pnl": round(pnl, 2), "date": t.get("trade_date", "")})

        total_pnl = round(sum(p["pnl"] for p in pnls), 2)
        wins = [p for p in pnls if p["pnl"] > 0]
        win_rate = round(len(wins) / len(pnls) * 100, 1)
        avg_pnl = round(total_pnl / len(pnls), 2)
        best = max(pnls, key=lambda x: x["pnl"])
        worst = min(pnls, key=lambda x: x["pnl"])

        return {
            "total_trades": len(pnls),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "best_trade": best,
            "worst_trade": worst,
        }
    except Exception as e:
        logger.error(f"Journal stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
