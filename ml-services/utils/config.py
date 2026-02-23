import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class to hold application settings."""
    
    # Database Configurations
    TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://admin:password@localhost:5432/marketmind")
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017/marketmind?authSource=admin")

    # MFlow Configuration
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    MODEL_REGISTRY_PATH = os.getenv("MODEL_REGISTRY_PATH", "./models")
    
    # External APIs
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
