from fastapi.testclient import TestClient
from api.main import app
import pytest

client = TestClient(app)

def test_compliance_headers():
    # Check if header is present on a random endpoint
    response = client.get("/api/status")
    assert response.status_code == 200
    assert "X-MarketMind-Disclaimer" in response.headers
    assert response.headers["X-MarketMind-Disclaimer"] == "Not Investment Advice. Educational Purpose Only."

def test_disclaimer_endpoint():
    response = client.get("/api/compliance/disclaimer")
    assert response.status_code == 200
    data = response.json()
    assert "disclaimer" in data
    assert "MarketMind AI is an educational tool" in data["disclaimer"]

def test_risk_endpoint():
    response = client.get("/api/compliance/risk")
    assert response.status_code == 200
    data = response.json()
    assert "risk_disclosure" in data
    assert "9 out of 10 individual traders" in data["risk_disclosure"]

if __name__ == "__main__":
    test_compliance_headers()
    print("Compliance headers OK")
    test_disclaimer_endpoint()
    print("Disclaimer endpoint OK")
    test_risk_endpoint()
    print("Risk endpoint OK")
