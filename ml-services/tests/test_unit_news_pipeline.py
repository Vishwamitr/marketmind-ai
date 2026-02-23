import mongomock
from news_pipeline.news_deduplicator import NewsDeduplicator
from news_pipeline.processor import NewsProcessor
from unittest.mock import MagicMock, patch
import pytest

@pytest.fixture
def mock_db():
    return mongomock.MongoClient().db

def test_deduplication(mock_db):
    # Setup mock data
    collection = mock_db.news_articles
    collection.insert_many([
        {"_id": 1, "title": "Market Rally"},
        {"_id": 2, "title": "Market Rally 2023"}, # Similar
        {"_id": 3, "title": "Different Topic"}
    ])
    
    deduplicator = NewsDeduplicator(db=mock_db)
    
    # Run finds
    # We need to verify that SequenceMatcher logic works
    # "Market Rally" vs "Market Rally 2023" -> Ratio ~0.8
    # "Market Rally" vs "Different Topic" -> Ratio < 0.5
    
    # We can invoke find_duplicates but we need to check if it updates the collection
    # Note: standard SequenceMatcher behavior is what we are testing alongside integration
    
    deduplicator.find_duplicates(threshold=0.5) # Low threshold to ensure match
    
    # Check if duplicate marked
    # Logic: Article 2 should be duplicate of Article 1 if loop works correctly
    # The loop compares i vs j. 
    # i=0 (Market Rally), j=1 (Market Rally 2023)
    # If match, update j
    
    updated_doc = collection.find_one({"_id": 2})
    assert updated_doc.get("is_duplicate") == True
    assert updated_doc.get("original_article_id") == 1
    
    # Article 3 should remain untouched
    doc_3 = collection.find_one({"_id": 3})
    assert not doc_3.get("is_duplicate")

def test_news_processor_sentiment(mock_db):
    collection = mock_db.news_articles
    collection.insert_one({
        "_id": 100,
        "title": "Great Earnings Report",
        "summary": "The company posted record profits."
        # No sentiment field initially
    })
    
    # Mock the Analyzer because it might load heavy models
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_text.return_value = {"score": 0.9, "label": "positive"}
    
    # Ensure dependencies are passed as keyword arguments or positional matching definition
    processor = NewsProcessor(db=mock_db, analyzer=mock_analyzer)

    # Mock bulk_write to avoid mongomock issues with UpdateOne
    collection.bulk_write = MagicMock()
    collection.bulk_write.return_value = MagicMock(modified_count=1)

    processor.process_new_articles()
    
    # Verify bulk_write called
    assert collection.bulk_write.called
    args = collection.bulk_write.call_args[0][0] # First arg is operations list
    assert len(args) == 1
    op = args[0]
    # Check if it's UpdateOne and has correct filter/update
    assert op._filter == {"_id": 100}
    assert op._doc == {"$set": {"sentiment": {"score": 0.9, "label": "positive"}}}

if __name__ == "__main__":
    pytest.main([__file__])
