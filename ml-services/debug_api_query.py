import pandas as pd
from data_pipeline.db_connector import DBConnector

def debug_query():
    db = DBConnector()
    symbol = 'INFY'
    limit = 5
    
    query = f"""
            SELECT sp.timestamp, sp.close, sp.volume, 
                   ti.sma_50, ti.sma_200, ti.rsi_14 as rsi, ti.macd, ti.macd_signal,
                   (ti.macd - ti.macd_signal) as macd_hist, ti.adx, ti.atr
            FROM stock_prices sp
            LEFT JOIN technical_indicators ti ON sp.timestamp = ti.timestamp AND sp.symbol = ti.symbol
            WHERE sp.symbol = '{symbol}'
            ORDER BY sp.timestamp DESC
            LIMIT {limit}
        """
    
    print("Executing query...")
    try:
        with DBConnector.get_connection() as conn:
            df = pd.read_sql(query, conn)
        print("Query Successful!")
        print(df.head())
    except Exception as e:
        print("Query Failed!")
        print(e)
        
        # Inspection
        print("\nInspecting technical_indicators columns:")
        try:
            with DBConnector.get_connection() as conn:
                insp = pd.read_sql("SELECT * FROM technical_indicators LIMIT 0", conn)
            print(insp.columns)
        except Exception as e2:
            print(e2)

if __name__ == "__main__":
    debug_query()
