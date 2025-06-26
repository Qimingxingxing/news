"""Models package for data structures."""

from .news import NewsSource, NewsArticle, NewsAPIResponse, PollingJobConfig
from .kafka import KafkaNewsMessage

__all__ = [
    "NewsSource",
    "NewsArticle", 
    "NewsAPIResponse",
    "PollingJobConfig",
    "KafkaNewsMessage"
] 