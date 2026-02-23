"""
Anomaly Detection Module — Detects volume spikes, price gaps, and unusual activity.
"""
import logging
import pandas as pd
import numpy as np
from data_pipeline.db_connector import DBConnector

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects market anomalies using statistical methods:
    - Volume spikes (Z-score based)
    - Price gaps (opening gap from previous close)
    - Regime changes (from regime history)
    - Unusual daily range (ATR-based)
    """

    def __init__(self, z_threshold: float = 2.5, gap_threshold: float = 0.03):
        """
        Args:
            z_threshold: Z-score threshold for anomaly detection (default 2.5 = ~99th percentile)
            gap_threshold: Minimum price gap percentage to flag (default 3%)
        """
        self.z_threshold = z_threshold
        self.gap_threshold = gap_threshold

    def detect_anomalies(self, symbol: str, lookback_days: int = 90) -> list:
        """
        Detect all types of anomalies for a given stock symbol.

        Returns:
            List of anomaly dicts with type, severity, timestamp, description.
        """
        anomalies = []

        try:
            query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM stock_prices
                WHERE symbol = '{symbol}'
                ORDER BY timestamp DESC
                LIMIT {lookback_days}
            """
            with DBConnector.get_connection() as conn:
                df = pd.read_sql(query, conn)

            if len(df) < 10:
                return []

            df = df.sort_values("timestamp").reset_index(drop=True)

            # 1. Volume Spikes
            anomalies.extend(self._detect_volume_spikes(df, symbol))

            # 2. Price Gaps
            anomalies.extend(self._detect_price_gaps(df, symbol))

            # 3. Unusual Daily Range
            anomalies.extend(self._detect_unusual_range(df, symbol))

            # 4. Sudden Price Moves
            anomalies.extend(self._detect_sudden_moves(df, symbol))

        except Exception as e:
            logger.error(f"Anomaly detection failed for {symbol}: {e}")

        # Sort by timestamp descending (most recent first)
        anomalies.sort(key=lambda a: a["timestamp"], reverse=True)
        return anomalies

    def _detect_volume_spikes(self, df: pd.DataFrame, symbol: str) -> list:
        """Detect days with abnormally high volume."""
        anomalies = []
        volumes = df["volume"].values.astype(float)
        mean_vol = np.mean(volumes)
        std_vol = np.std(volumes)

        if std_vol == 0:
            return []

        z_scores = (volumes - mean_vol) / std_vol

        for i, z in enumerate(z_scores):
            if z > self.z_threshold:
                severity = "high" if z > 4 else "medium"
                anomalies.append({
                    "type": "volume_spike",
                    "severity": severity,
                    "symbol": symbol,
                    "timestamp": str(df["timestamp"].iloc[i]),
                    "description": f"Volume {volumes[i]/mean_vol:.1f}x above average (Z-score: {z:.1f})",
                    "value": float(volumes[i]),
                    "z_score": round(float(z), 2),
                })

        return anomalies

    def _detect_price_gaps(self, df: pd.DataFrame, symbol: str) -> list:
        """Detect opening gaps from previous close."""
        anomalies = []
        for i in range(1, len(df)):
            prev_close = float(df["close"].iloc[i - 1])
            curr_open = float(df["open"].iloc[i])

            if prev_close == 0:
                continue

            gap_pct = (curr_open - prev_close) / prev_close

            if abs(gap_pct) > self.gap_threshold:
                direction = "up" if gap_pct > 0 else "down"
                anomalies.append({
                    "type": f"gap_{direction}",
                    "severity": "high" if abs(gap_pct) > 0.05 else "medium",
                    "symbol": symbol,
                    "timestamp": str(df["timestamp"].iloc[i]),
                    "description": f"Gap {direction} of {abs(gap_pct)*100:.1f}% (₹{prev_close:.2f} → ₹{curr_open:.2f})",
                    "value": round(gap_pct * 100, 2),
                })

        return anomalies

    def _detect_unusual_range(self, df: pd.DataFrame, symbol: str) -> list:
        """Detect days with unusually wide high-low range."""
        anomalies = []
        df_copy = df.copy()
        df_copy["range"] = (df_copy["high"] - df_copy["low"]).astype(float)
        df_copy["range_pct"] = df_copy["range"] / df_copy["close"].astype(float) * 100

        mean_range = df_copy["range_pct"].mean()
        std_range = df_copy["range_pct"].std()

        if std_range == 0:
            return []

        for i, row in df_copy.iterrows():
            z = (row["range_pct"] - mean_range) / std_range
            if z > self.z_threshold:
                anomalies.append({
                    "type": "unusual_range",
                    "severity": "medium",
                    "symbol": symbol,
                    "timestamp": str(row["timestamp"]),
                    "description": f"Daily range {row['range_pct']:.1f}% (avg: {mean_range:.1f}%)",
                    "value": round(float(row["range_pct"]), 2),
                    "z_score": round(float(z), 2),
                })

        return anomalies

    def _detect_sudden_moves(self, df: pd.DataFrame, symbol: str) -> list:
        """Detect large single-day price moves."""
        anomalies = []
        for i in range(1, len(df)):
            prev_close = float(df["close"].iloc[i - 1])
            curr_close = float(df["close"].iloc[i])

            if prev_close == 0:
                continue

            daily_return = (curr_close - prev_close) / prev_close * 100

            if abs(daily_return) > 5:
                direction = "surge" if daily_return > 0 else "crash"
                anomalies.append({
                    "type": f"price_{direction}",
                    "severity": "high" if abs(daily_return) > 8 else "medium",
                    "symbol": symbol,
                    "timestamp": str(df["timestamp"].iloc[i]),
                    "description": f"Price {direction}: {daily_return:+.1f}% in a single day",
                    "value": round(daily_return, 2),
                })

        return anomalies


def detect_all_anomalies(lookback_days: int = 60) -> list:
    """
    Run anomaly detection across ALL tracked stocks.
    Returns aggregated anomalies sorted by timestamp (most recent first).
    """
    detector = AnomalyDetector()
    all_anomalies = []

    try:
        query = "SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol"
        with DBConnector.get_connection() as conn:
            df = pd.read_sql(query, conn)

        for symbol in df["symbol"].tolist():
            anomalies = detector.detect_anomalies(symbol, lookback_days)
            all_anomalies.extend(anomalies)

    except Exception as e:
        logger.error(f"Batch anomaly detection failed: {e}")

    all_anomalies.sort(key=lambda a: a["timestamp"], reverse=True)
    return all_anomalies
