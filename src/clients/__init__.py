"""Clients package for external API integrations."""

from .news_api_client import NewsAPIClient
from .kafka_client import NewsKafkaProducer
from .redis_client import NewsRedisClient

__all__ = [
    "NewsAPIClient",
    "NewsKafkaProducer",
    "NewsRedisClient"
] 