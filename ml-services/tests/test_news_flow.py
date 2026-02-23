import requests
import time

BASE_URL = "http://localhost:8000"

def run_test():
    print("Testing News API...")

    # 1. Get News (Empty ok/expected if no scraper ran)
    resp = requests.get(f"{BASE_URL}/api/news", params={"limit": 5})
    print(f"Get News: {resp.status_code}")
    assert resp.status_code == 200
    articles = resp.json()
    print(f"Articles found: {len(articles)}")
    if len(articles) > 0:
        print(f"Sample: {articles[0].get('title')}")

    # 2. Get Sentiment Trend
    # We query for a symbol that likely won't exist but ensures 200 OK and empty list
    resp = requests.get(f"{BASE_URL}/api/news/sentiment_trend", params={"symbol": "TEST_SYM"})
    print(f"Get Trend: {resp.status_code}")
    assert resp.status_code == 200
    trend = resp.json()
    print(f"Trend data points: {len(trend)}")
    assert isinstance(trend, list)

if __name__ == "__main__":
    run_test()
