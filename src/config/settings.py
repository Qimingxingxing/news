"""Configuration management for the news polling service."""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # NewsAPI Configuration
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    NEWS_API_BASE_URL = "https://newsapi.org/v2"
    NEWS_API_ENDPOINTS = {
        "top_headlines": "/top-headlines",
        "everything": "/everything",
        "sources": "/sources"
    }
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_NEWS = os.getenv("KAFKA_TOPIC_NEWS", "news-articles")
    KAFKA_TOPIC_RAW_NEWS = os.getenv("KAFKA_TOPIC_RAW_NEWS", "raw-news")
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DEDUP_KEY_PREFIX = os.getenv("REDIS_DEDUP_KEY_PREFIX", "news:dedup")
    REDIS_DEDUP_TTL_HOURS = int(os.getenv("REDIS_DEDUP_TTL_HOURS", "24"))
    
    # Article Scraping Configuration
    ENABLE_ARTICLE_SCRAPING = os.getenv("ENABLE_ARTICLE_SCRAPING", "true").lower() == "true"
    SCRAPING_TIMEOUT = int(os.getenv("SCRAPING_TIMEOUT", "10"))
    SCRAPING_MAX_RETRIES = int(os.getenv("SCRAPING_MAX_RETRIES", "3"))
    SCRAPING_RATE_LIMIT_DELAY = float(os.getenv("SCRAPING_RATE_LIMIT_DELAY", "0.5"))
    
    # Polling Configuration
    POLLING_INTERVAL_MINUTES = int(os.getenv("POLLING_INTERVAL_MINUTES", "15"))
    MAX_ARTICLES_PER_REQUEST = int(os.getenv("MAX_ARTICLES_PER_REQUEST", "100"))
    
    # News Sources Configuration
    DEFAULT_COUNTRIES = ["us", "gb", "ca", "au"]
    DEFAULT_CATEGORIES = ["business", "technology", "science", "health"]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    
    @classmethod
    def get_kafka_config(cls) -> Dict[str, Any]:
        """Get Kafka producer configuration."""
        return {
            "bootstrap.servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "news-polling-service",
            "acks": "all",
            "retries": 3,
            "batch.size": 16384,
            "linger.ms": 10
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.NEWS_API_KEY:
            raise ValueError("NEWS_API_KEY environment variable is required")
        return True 