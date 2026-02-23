from locust import HttpUser, task, between, tag

class MarketMindUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Log in to get a token
        response = self.client.post("/api/auth/login", data={"username": "testuser", "password": "testpassword"})
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    @tag("public")
    def get_latest_market_data(self):
        # High traffic endpoint
        self.client.get("/api/market/latest/AAPL")

    @task(1)
    @tag("heavy")
    def get_market_history(self):
        # heavier endpoint
        self.client.get("/api/market/history/AAPL?limit=50")

    @task(2)
    @tag("news")
    def get_news(self):
        self.client.get("/api/news?symbol=AAPL")

    @task(1)
    @tag("protected")
    def get_portfolio(self):
        if self.token:
            self.client.get("/api/portfolio", headers=self.headers)
