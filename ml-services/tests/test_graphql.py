from fastapi.testclient import TestClient
from api.main import app
import pytest

client = TestClient(app)

def test_graphql_stocks():
    query = """
    query {
        stocks(limit: 2) {
            symbol
            currentPrice
        }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "stocks" in data["data"]
    assert len(data["data"]["stocks"]) == 2
    assert "symbol" in data["data"]["stocks"][0]
    # Verify field masking (volume should NOT be here)
    assert "volume" not in data["data"]["stocks"][0]

def test_graphql_news():
    query = """
    query {
        news(limit: 1) {
            title
            sentimentScore
        }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]["news"]) == 1

if __name__ == "__main__":
    test_graphql_stocks()
    print("GraphQL Stocks OK")
    test_graphql_news()
    print("GraphQL News OK")
