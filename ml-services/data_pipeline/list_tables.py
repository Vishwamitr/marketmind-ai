from data_pipeline.db_connector import DBConnector
import pandas as pd

def list_tables():
    with DBConnector.get_connection() as conn:
        print("--- Tables ---")
        tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", conn)
        print(tables)
        
        # Check if 'model_metrics' or similar exists
        if 'model_metrics' in tables['table_name'].values:
            print("\n--- Model Metrics Structure ---")
            df = pd.read_sql("SELECT * FROM model_metrics LIMIT 1", conn)
            print(df.columns.tolist())
        else:
            print("\nmodel_metrics table NOT found.")

if __name__ == "__main__":
    list_tables()
