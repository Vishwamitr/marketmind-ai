import sys
import os

# Add ml-services to path
sys.path.append(os.getcwd())

try:
    from utils.config import Config
    print("Import utils.config: SUCCESS")
except ImportError as e:
    print(f"Import utils.config: FAILED - {e}")

try:
    from data_pipeline.db_connector import DBConnector
    print("Import data_pipeline.db_connector: SUCCESS")
except ImportError as e:
    print(f"Import data_pipeline.db_connector: FAILED - {e}")

try:
    import psycopg2
    print("Import psycopg2: SUCCESS")
except ImportError as e:
    print(f"Import psycopg2: FAILED - {e}")
