"""
Price Alert System — CRUD API + SQLite storage.
Supports price-above, price-below, rsi-above, rsi-below, volume-spike conditions.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import logging
import time
import os

router = APIRouter()
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "alerts.db")


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            condition TEXT NOT NULL,
            threshold REAL NOT NULL,
            status TEXT DEFAULT 'active',
            created_at REAL NOT NULL,
            triggered_at REAL,
            current_value REAL,
            note TEXT DEFAULT ''
        )
    """)
    conn.commit()
    return conn


class AlertCreate(BaseModel):
    symbol: str
    condition: str  # price_above, price_below, rsi_above, rsi_below, volume_spike
    threshold: float
    note: Optional[str] = ""


@router.post("/alerts")
def create_alert(alert: AlertCreate):
    """Create a new price/technical alert."""
    valid_conditions = ["price_above", "price_below", "rsi_above", "rsi_below", "volume_spike"]
    if alert.condition not in valid_conditions:
        raise HTTPException(status_code=400, detail=f"Invalid condition. Use: {valid_conditions}")

    conn = _get_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO alerts (symbol, condition, threshold, created_at, note) VALUES (?, ?, ?, ?, ?)",
            (alert.symbol.upper(), alert.condition, alert.threshold, time.time(), alert.note or ""),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "status": "created", "symbol": alert.symbol.upper()}
    finally:
        conn.close()


@router.get("/alerts")
def list_alerts(status: str = "active"):
    """List alerts filtered by status (active/triggered/all)."""
    conn = _get_conn()
    try:
        if status == "all":
            rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        return {"alerts": [dict(r) for r in rows], "total": len(rows)}
    finally:
        conn.close()


@router.get("/alerts/triggered")
def list_triggered():
    """List recently triggered alerts."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE status = 'triggered' ORDER BY triggered_at DESC LIMIT 50"
        ).fetchall()
        return {"alerts": [dict(r) for r in rows], "total": len(rows)}
    finally:
        conn.close()


@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int):
    """Delete an alert by ID."""
    conn = _get_conn()
    try:
        cursor = conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "deleted", "id": alert_id}
    finally:
        conn.close()


@router.post("/alerts/check")
def check_alerts():
    """Check all active alerts against current market data. Triggers matching alerts."""
    import yfinance as yf

    conn = _get_conn()
    try:
        rows = conn.execute("SELECT * FROM alerts WHERE status = 'active'").fetchall()
        triggered = []

        # Group by symbol to minimize API calls
        symbols = set(dict(r)["symbol"] for r in rows)
        price_cache: dict = {}

        for sym in symbols:
            try:
                t = yf.Ticker(f"{sym}.NS")
                hist = t.history(period="5d")
                if hist is not None and not hist.empty:
                    price_cache[sym] = {
                        "price": float(hist["Close"].iloc[-1]),
                        "volume": int(hist["Volume"].iloc[-1]),
                        "avg_volume": int(hist["Volume"].mean()),
                    }
            except Exception:
                continue

        for row in rows:
            alert = dict(row)
            sym = alert["symbol"]
            if sym not in price_cache:
                continue

            data = price_cache[sym]
            condition = alert["condition"]
            threshold = alert["threshold"]
            is_triggered = False
            current_value = 0.0

            if condition == "price_above" and data["price"] >= threshold:
                is_triggered = True
                current_value = data["price"]
            elif condition == "price_below" and data["price"] <= threshold:
                is_triggered = True
                current_value = data["price"]
            elif condition == "volume_spike":
                ratio = data["volume"] / data["avg_volume"] if data["avg_volume"] > 0 else 0
                if ratio >= threshold:
                    is_triggered = True
                    current_value = round(ratio, 2)

            if is_triggered:
                conn.execute(
                    "UPDATE alerts SET status = 'triggered', triggered_at = ?, current_value = ? WHERE id = ?",
                    (time.time(), current_value, alert["id"]),
                )
                triggered.append({**alert, "current_value": current_value})

        conn.commit()
        return {"checked": len(rows), "triggered": len(triggered), "triggered_alerts": triggered}
    finally:
        conn.close()
