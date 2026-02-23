import requests
import psycopg2
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000"
DB_URL = "postgresql://user:password@localhost:5432/marketmind" # Adjust if needed, or use DBConnector logic

def run_test():
    symbol = "MONITOR_TEST"
    model = "TestModel"
    # Use a time in the past
    ts = (datetime.now() - timedelta(hours=1)).replace(microsecond=0, second=0, minute=0)
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Testing with symbol {symbol} at {ts_str}")

    # 1. Insert Dummy Stock Price directly to DB (bypassing API to ensure existence)
    # We need to use the actual DB credentials. 
    # Since we can't easily import DBConnector here without environment setup, 
    # we'll rely on the API if possible, or assume the environment is set up for the script.
    # actually, let's use the internal DBConnector by running this as a module.
    
    from data_pipeline.db_connector import DBConnector
    
    with DBConnector.get_connection() as conn:
        with conn.cursor() as cur:
            # Clean up prev test
            cur.execute("DELETE FROM stock_prices WHERE symbol = %s", (symbol,))
            cur.execute("DELETE FROM model_predictions WHERE symbol = %s", (symbol,))
            cur.execute("DELETE FROM model_metrics WHERE symbol = %s", (symbol,))
            
            # Insert Price: 100.0
            cur.execute("""
                INSERT INTO stock_prices (symbol, open, high, low, close, volume, timestamp, exchange)
                VALUES (%s, 100, 110, 90, 100.0, 1000, %s, 'NSE')
            """, (symbol, ts))
            conn.commit()
            print("Inserted dummy stock price: 100.0")

    # 2. Log Prediction: 105.0 (Error = 5.0)
    resp = requests.post(f"{BASE_URL}/api/monitor/log_prediction", params={
        "model": model,
        "symbol": symbol,
        "price": 105.0,
        "timestamp": ts_str
    })
    print(f"Log Prediction: {resp.status_code} - {resp.json()}")
    assert resp.status_code == 200

    # 3. Calculate Metrics
    resp = requests.post(f"{BASE_URL}/api/monitor/calculate")
    print(f"Calculate: {resp.status_code} - {resp.json()}")
    assert resp.status_code == 200
    assert resp.json()['updated_rows'] >= 1

    # 4. Get Metrics
    resp = requests.get(f"{BASE_URL}/api/monitor/metrics", params={"model": model, "symbol": symbol})
    print(f"Get Metrics: {resp.status_code} - {resp.json()}")
    data = resp.json()
    
    assert len(data) > 0
    mae_metric = next((m for m in data if m['metric_name'] == 'MAE'), None)
    assert mae_metric is not None
    print(f"MAE: {mae_metric['value']}")
    assert abs(mae_metric['value'] - 5.0) < 0.001

if __name__ == "__main__":
    run_test()
