"""Kafka-related data models."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from .news import NewsArticle


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