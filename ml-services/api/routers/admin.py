from fastapi import APIRouter, HTTPException, Depends
import psutil
import pandas as pd
from data_pipeline.mongo_connector import MongoConnector
from data_pipeline.db_connector import DBConnector
from api.auth_utils import get_current_active_user, User

router = APIRouter()

@router.get("/admin/stats")
def get_admin_stats(current_user: User = Depends(get_current_active_user)):
    try:
        # 1. System Stats
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        
        # 2. Database Stats
        stats = {
            "system": {
                "cpu": cpu_percent,
                "ram": ram_percent,
                "status": "Healthy" # Placeholder for DB check
            },
            "counts": {}
        }
        
        with DBConnector.get_connection() as conn:
            # PostgreSQL Counts
            count_queries = {
                "stocks_tracked": "SELECT COUNT(DISTINCT symbol) FROM stock_prices",
                "total_prices": "SELECT COUNT(*) FROM stock_prices",
                "total_transactions": "SELECT COUNT(*) FROM transactions",
                "portfolio_value": "SELECT cash FROM portfolio_balance WHERE id = 1"
            }
            
            with conn.cursor() as cur:
                for key, q in count_queries.items():
                    cur.execute(q)
                    res = cur.fetchone()
                    stats["counts"][key] = res[0] if res else 0

        # MongoDB Counts
        try:
            db = MongoConnector.get_db()
            stats["counts"]["news_articles"] = db.news_articles.count_documents({})
            stats["counts"]["predictions"] = db.model_predictions.count_documents({}) # If using Mongo for logs? Actually preds are in PG
            # Check for logs collection if exists
            if "logs" in db.list_collection_names():
                 stats["counts"]["system_logs"] = db.logs.count_documents({})
            else:
                 stats["counts"]["system_logs"] = 0
        except Exception:
             stats["counts"]["news_articles"] = -1 # Error indicator

        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/logs")
def get_admin_logs(limit: int = 50, current_user: User = Depends(get_current_active_user)):
    try:
        # Return recent transactions as "Activity Logs" for now
        with DBConnector.get_connection() as conn:
            query = """
                SELECT id, timestamp, symbol, action, quantity, price 
                FROM transactions 
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(limit,))
            
            # Convert to list of dicts with standardized fields
            logs = []
            for _, row in df.iterrows():
                logs.append({
                    "id": row['id'],
                    "timestamp": row['timestamp'].isoformat(),
                    "level": "INFO",
                    "source": "UserOrder",
                    "message": f"{row['action']} {row['quantity']} {row['symbol']} @ {row['price']}"
                })
                
            return logs
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
