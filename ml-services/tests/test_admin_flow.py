import requests
import time

BASE_URL = "http://localhost:8000"

def run_test():
    print("Testing Admin API...")

    # 1. Get Stats
    resp = requests.get(f"{BASE_URL}/api/admin/stats")
    print(f"Get Stats: {resp.status_code}")
    assert resp.status_code == 200
    stats = resp.json()
    
    print("System Health:")
    print(f"  CPU: {stats['system']['cpu']}%")
    print(f"  RAM: {stats['system']['ram']}%")
    
    print("Counts:")
    for k, v in stats['counts'].items():
        print(f"  {k}: {v}")
        
    assert 'total_transactions' in stats['counts']

    # 2. Get Logs
    resp = requests.get(f"{BASE_URL}/api/admin/logs")
    print(f"Get Logs: {resp.status_code}")
    assert resp.status_code == 200
    logs = resp.json()
    print(f"Logs retrieved: {len(logs)}")
    
    if len(logs) > 0:
        print(f"Sample Log: {logs[0]['message']}")

if __name__ == "__main__":
    run_test()
