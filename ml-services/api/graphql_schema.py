import strawberry
from typing import List, Optional
from datetime import datetime
import random

# Define Types
@strawberry.type
class Stock:
    symbol: str
    company_name: str
    current_price: float
    day_high: float
    day_low: float
    volume: int

@strawberry.type
class NewsHelper:
    title: str
    summary: str
    source: str
    published_at: str
    sentiment_score: float

# Define Resolvers (Mock data for now, would connect to DB/Mongo in real impl)
def get_stocks(limit: int = 10) -> List[Stock]:
    symbols = ["INFY", "TCS", "RELIANCE", "WIPRO", "HDFCBANK"]
    stocks = []
    for i in range(min(limit, len(symbols))):
        s = symbols[i]
        price = 1000 + random.uniform(-50, 50)
        stocks.append(Stock(
            symbol=s,
            company_name=f"{s} Ltd",
            current_price=round(price, 2),
            day_high=round(price * 1.02, 2),
            day_low=round(price * 0.98, 2),
            volume=random.randint(10000, 1000000)
        ))
    return stocks

def get_stock(symbol: str) -> Optional[Stock]:
    price = 1500.0
    return Stock(
        symbol=symbol,
        company_name=f"{symbol} Ltd",
        current_price=price,
        day_high=price + 20,
        day_low=price - 20,
        volume=50000
    )

def get_news(limit: int = 5) -> List[NewsHelper]:
    news = []
    for i in range(limit):
        news.append(NewsHelper(
            title=f"News Headline {i+1}",
            summary="This is a summary of the news article...",
            source="Financial Express",
            published_at=datetime.isoformat(datetime.now()),
            sentiment_score=random.uniform(-1, 1)
        ))
    return news

# Define Query
@strawberry.type
class Query:
    stocks: List[Stock] = strawberry.field(resolver=get_stocks)
    stock: Optional[Stock] = strawberry.field(resolver=get_stock)
    news: List[NewsHelper] = strawberry.field(resolver=get_news)

schema = strawberry.Schema(query=Query)
