"""Redis client for news deduplication."""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional
import redis
from loguru import logger

from ..config import Config


class NewsRedisClient:
    """Redis client for news deduplication and caching."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Redis client.
        
        Args:
            config: Redis configuration dictionary. If None, uses default config.
        """
        self.config = config or self._get_redis_config()
        self.client = redis.Redis(**self.config)
        self.dedup_prefix = Config.REDIS_DEDUP_KEY_PREFIX
        self.dedup_ttl = Config.REDIS_DEDUP_TTL_HOURS * 3600  # Convert hours to seconds
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {self.config['host']}:{self.config['port']}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration from settings."""
        config = {
            'host': Config.REDIS_HOST,
            'port': Config.REDIS_PORT,
            'db': Config.REDIS_DB,
            'decode_responses': True,  # Return strings instead of bytes
            'socket_connect_timeout': 5,
            'socket_timeout': 5,
        }
        
        if Config.REDIS_PASSWORD:
            config['password'] = Config.REDIS_PASSWORD
        
        return config
    
    def _generate_dedup_key(self, title: str, source: str) -> str:
        """Generate a deduplication key for a news article.
        
        Args:
            title: Article title
            source: News source name
            
        Returns:
            Redis key for deduplication
        """
        # Create a hash of title + source for consistent key generation
        content = f"{title.lower().strip()}:{source.lower().strip()}"
        hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"{self.dedup_prefix}:{hash_value}"
    
    def is_duplicate(self, title: str, source: str) -> bool:
        """Check if a news article is a duplicate based on title and source.
        
        Args:
            title: Article title
            source: News source name
            
        Returns:
            True if article is a duplicate, False otherwise
        """
        try:
            key = self._generate_dedup_key(title, source)
            exists = self.client.exists(key)
            
            if exists:
                logger.debug(f"Duplicate found: {title[:50]}... from {source}")
            else:
                logger.debug(f"New article: {title[:50]}... from {source}")
            
            return bool(exists)
            
        except redis.RedisError as e:
            logger.error(f"Redis error checking duplicate: {e}")
            # If Redis is unavailable, assume not duplicate to avoid blocking
            return False
    
    def mark_as_seen(self, title: str, source: str, article_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark a news article as seen (stored in Redis).
        
        Args:
            title: Article title
            source: News source name
            article_data: Optional article data to store
        """
        try:
            key = self._generate_dedup_key(title, source)
            
            # Store article data or just timestamp
            if article_data:
                value = json.dumps({
                    'title': title,
                    'source': source,
                    'seen_at': time.time(),
                    'data': article_data
                })
            else:
                value = json.dumps({
                    'title': title,
                    'source': source,
                    'seen_at': time.time()
                })
            
            # Set with TTL
            self.client.setex(key, self.dedup_ttl, value)
            logger.debug(f"Marked as seen: {title[:50]}... from {source}")
            
        except redis.RedisError as e:
            logger.error(f"Redis error marking as seen: {e}")
    
    def filter_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out duplicate articles from a list.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of articles with duplicates removed
        """
        if not articles:
            return []
        
        unique_articles = []
        duplicates_count = 0
        
        for article in articles:
            title = article.get('title', '')
            source_name = article.get('source', {}).get('name', 'unknown')
            
            if not title or not source_name:
                logger.warning(f"Article missing title or source: {article}")
                continue
            
            if self.is_duplicate(title, source_name):
                duplicates_count += 1
                continue
            
            # Mark as seen and add to unique list
            self.mark_as_seen(title, source_name, article)
            unique_articles.append(article)
        
        if duplicates_count > 0:
            logger.info(f"Filtered out {duplicates_count} duplicate articles")
        
        logger.info(f"Returning {len(unique_articles)} unique articles from {len(articles)} total")
        return unique_articles
    
    def get_dedup_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics.
        
        Returns:
            Dictionary with deduplication statistics
        """
        try:
            pattern = f"{self.dedup_prefix}:*"
            keys = self.client.keys(pattern)
            
            stats = {
                'total_dedup_keys': len(keys),
                'dedup_prefix': self.dedup_prefix,
                'ttl_hours': Config.REDIS_DEDUP_TTL_HOURS
            }
            
            # Get some sample keys for debugging
            if keys:
                sample_keys = keys[:5]
                stats['sample_keys'] = sample_keys
            
            return stats
            
        except redis.RedisError as e:
            logger.error(f"Redis error getting stats: {e}")
            return {'error': str(e)}
    
    def clear_dedup_cache(self) -> bool:
        """Clear all deduplication cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            pattern = f"{self.dedup_prefix}:*"
            keys = self.client.keys(pattern)
            
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} deduplication cache entries")
                return True
            else:
                logger.info("No deduplication cache entries to clear")
                return True
                
        except redis.RedisError as e:
            logger.error(f"Redis error clearing cache: {e}")
            return False
    
    def close(self) -> None:
        """Close the Redis connection."""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 