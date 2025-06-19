"""Data models for news articles."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NewsSource(BaseModel):
    """Model for news source information."""
    id: Optional[str] = None
    name: str


class NewsArticle(BaseModel):
    """Model for a news article."""
    source: NewsSource
    author: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: str
    url_to_image: Optional[str] = None
    published_at: datetime
    content: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsAPIResponse(BaseModel):
    """Model for NewsAPI response."""
    status: str
    total_results: int
    articles: List[NewsArticle]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KafkaNewsMessage(BaseModel):
    """Model for Kafka message containing news data."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    country: Optional[str] = None
    category: Optional[str] = None
    articles: List[NewsArticle]
    total_results: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PollingJobConfig(BaseModel):
    """Configuration for polling job."""
    countries: List[str] = ["us", "gb", "ca", "au"]
    categories: List[str] = ["business", "technology", "science", "health"]
    interval_minutes: int = 15
    max_articles: int = 100 