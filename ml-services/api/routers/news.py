"""
News & Sentiment API — Fetches financial news with RSS fallback.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


def _fetch_rss_news(query: str = "India stock market", limit: int = 20):
    """Fetch financial news from Google News RSS as a free fallback."""
    import urllib.request
    import html

    feeds = [
        f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' stock market')}&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
    ]

    articles = []
    for feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketMind/1.0)"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read().decode("utf-8")

            root = ET.fromstring(xml_data)
            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                source_el = item.find("source")
                source = source_el.text if source_el is not None else "Google News"
                description = item.findtext("description", "")

                # Clean HTML from description
                clean_desc = html.unescape(description)
                # Strip HTML tags simply
                import re
                clean_desc = re.sub(r"<[^>]+>", "", clean_desc).strip()

                # Parse date
                try:
                    dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                    published_at = dt.isoformat()
                except Exception:
                    published_at = pub_date

                # Simple sentiment heuristic based on keywords
                title_lower = title.lower()
                if any(w in title_lower for w in ["surge", "rally", "gain", "rise", "jump", "bull", "high", "record", "profit", "up"]):
                    sentiment = {"label": "positive", "score": 0.75}
                elif any(w in title_lower for w in ["crash", "fall", "drop", "loss", "bear", "down", "fear", "decline", "slump", "tank"]):
                    sentiment = {"label": "negative", "score": 0.70}
                else:
                    sentiment = {"label": "neutral", "score": 0.50}

                articles.append({
                    "title": html.unescape(title),
                    "summary": clean_desc[:300] if clean_desc else "",
                    "published_at": published_at,
                    "source": source,
                    "link": link,
                    "sentiment": sentiment,
                })

                if len(articles) >= limit:
                    break

        except Exception as e:
            logger.warning(f"RSS fetch failed for {feed_url}: {e}")
            continue

        if len(articles) >= limit:
            break

    return articles[:limit]


@router.get("/news")
def get_news(limit: int = 20, symbol: Optional[str] = None):
    """Get financial news. Uses MongoDB if available, falls back to RSS."""
    # Try MongoDB first
    try:
        from data_pipeline.mongo_connector import MongoConnector
        db = MongoConnector.get_db()
        collection = db.news_articles

        query = {}
        if symbol:
            query["$or"] = [
                {"title": {"$regex": symbol, "$options": "i"}},
                {"summary": {"$regex": symbol, "$options": "i"}}
            ]

        cursor = collection.find(query, {"_id": 0}).sort("published_at", -1).limit(limit)
        articles = list(cursor)

        if articles:
            return articles
    except Exception as e:
        logger.info(f"MongoDB unavailable, using RSS fallback: {e}")

    # Fallback: RSS feeds
    try:
        search_term = symbol if symbol else "India"
        articles = _fetch_rss_news(search_term, limit)
        return articles
    except Exception as e:
        logger.error(f"RSS fallback also failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news from any source")


@router.get("/news/sentiment_trend")
def get_sentiment_trend(symbol: str):
    """Get sentiment trend. Uses MongoDB if available, generates from RSS otherwise."""
    # Try MongoDB first
    try:
        from data_pipeline.mongo_connector import MongoConnector
        db = MongoConnector.get_db()
        collection = db.news_articles

        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"title": {"$regex": symbol, "$options": "i"}},
                        {"summary": {"$regex": symbol, "$options": "i"}}
                    ],
                    "sentiment": {"$exists": True}
                }
            },
            {
                "$project": {
                    "date": {"$substr": ["$published_at", 0, 10]},
                    "score": "$sentiment.score",
                    "label": "$sentiment.label"
                }
            },
            {
                "$group": {
                    "_id": "$date",
                    "avg_score": {"$avg": "$score"},
                    "count": {"$sum": 1},
                    "positive_count": {
                        "$sum": {"$cond": [{"$eq": ["$label", "positive"]}, 1, 0]}
                    },
                    "negative_count": {
                        "$sum": {"$cond": [{"$eq": ["$label", "negative"]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]

        trend = list(collection.aggregate(pipeline))
        if trend:
            return trend
    except Exception as e:
        logger.info(f"MongoDB unavailable for sentiment trend: {e}")

    # Fallback: generate trend from RSS articles
    try:
        articles = _fetch_rss_news(symbol, 50)
        # Group by date
        daily = {}
        for art in articles:
            date_str = art["published_at"][:10] if art.get("published_at") else "unknown"
            if date_str not in daily:
                daily[date_str] = {"scores": [], "positive": 0, "negative": 0}
            sent = art.get("sentiment", {})
            daily[date_str]["scores"].append(sent.get("score", 0.5))
            if sent.get("label") == "positive":
                daily[date_str]["positive"] += 1
            elif sent.get("label") == "negative":
                daily[date_str]["negative"] += 1

        trend = []
        for date_key in sorted(daily.keys()):
            d = daily[date_key]
            trend.append({
                "_id": date_key,
                "avg_score": round(sum(d["scores"]) / len(d["scores"]), 3) if d["scores"] else 0.5,
                "count": len(d["scores"]),
                "positive_count": d["positive"],
                "negative_count": d["negative"],
            })
        return trend
    except Exception as e:
        logger.error(f"Sentiment trend fallback failed: {e}")
        return []


@router.get("/news/sentiment/{symbol}")
def get_stock_sentiment(symbol: str, limit: int = 20):
    """
    Get aggregated sentiment analysis for a specific stock.
    """
    # Try MongoDB first
    try:
        from data_pipeline.mongo_connector import MongoConnector
        db = MongoConnector.get_db()
        collection = db.news_articles

        query = {
            "$or": [
                {"title": {"$regex": symbol, "$options": "i"}},
                {"summary": {"$regex": symbol, "$options": "i"}}
            ]
        }
        cursor = collection.find(query, {"_id": 0}).sort("published_at", -1).limit(limit)
        articles = list(cursor)

        if articles:
            sentiments = [a["sentiment"] for a in articles if "sentiment" in a]
            if sentiments:
                avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
                positive = sum(1 for s in sentiments if s["label"] == "positive")
                negative = sum(1 for s in sentiments if s["label"] == "negative")
                neutral = sum(1 for s in sentiments if s["label"] == "neutral")
                overall = "positive" if positive > negative else "negative" if negative > positive else "neutral"
            else:
                avg_score = 0
                positive = negative = neutral = 0
                overall = "unknown"

            return {
                "symbol": symbol.upper(),
                "overall_sentiment": overall,
                "avg_score": round(avg_score, 3),
                "article_count": len(articles),
                "sentiment_count": len(sentiments),
                "breakdown": {"positive": positive, "negative": negative, "neutral": neutral},
                "articles": articles,
            }
    except Exception as e:
        logger.info(f"MongoDB unavailable for stock sentiment: {e}")

    # Fallback: use RSS
    try:
        articles = _fetch_rss_news(symbol, limit)
        sentiments = [a["sentiment"] for a in articles if "sentiment" in a]
        if sentiments:
            avg_score = sum(s["score"] for s in sentiments) / len(sentiments)
            positive = sum(1 for s in sentiments if s["label"] == "positive")
            negative = sum(1 for s in sentiments if s["label"] == "negative")
            neutral = sum(1 for s in sentiments if s["label"] == "neutral")
            overall = "positive" if positive > negative else "negative" if negative > positive else "neutral"
        else:
            avg_score = 0.5
            positive = negative = neutral = 0
            overall = "unknown"

        return {
            "symbol": symbol.upper(),
            "overall_sentiment": overall,
            "avg_score": round(avg_score, 3),
            "article_count": len(articles),
            "sentiment_count": len(sentiments),
            "breakdown": {"positive": positive, "negative": negative, "neutral": neutral},
            "articles": articles,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
