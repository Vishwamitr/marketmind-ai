from data_pipeline.db_connector import DBConnector
import pandas as pd

def check():
    with DBConnector.get_connection() as conn:
        print("--- Portfolio Balance ---")
        df_cash = pd.read_sql("SELECT * FROM portfolio_balance", conn)
        print(df_cash)
        
        print("\n--- Holdings ---")
        df_holdings = pd.read_sql("SELECT * FROM holdings", conn)
        print(df_holdings)
        
        print("\n--- Transactions ---")
        df_tx = pd.read_sql("SELECT * FROM transactions", conn)
        print(df_tx)

if __name__ == "__main__":
    check()
