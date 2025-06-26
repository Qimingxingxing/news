"""Kafka producer for news data."""

import json
import time
from typing import Dict, Any, Optional, Callable
from confluent_kafka import Producer, KafkaError, KafkaException
from loguru import logger

from ..config import Config
from ..models import KafkaNewsMessage


class NewsKafkaProducer:
    """Kafka producer for publishing news data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Kafka producer.
        
        Args:
            config: Kafka configuration dictionary. If None, uses default config.
        """
        self.config = config or Config.get_kafka_config()
        self.producer = Producer(self.config)
        self.topic_news = Config.KAFKA_TOPIC_NEWS
        self.topic_raw_news = Config.KAFKA_TOPIC_RAW_NEWS
        
        logger.info(f"Initialized Kafka producer with bootstrap servers: {self.config['bootstrap.servers']}")
    
    def delivery_callback(self, err: Optional[KafkaError], msg: Any) -> None:
        """Callback function for message delivery confirmation.
        
        Args:
            err: Kafka error if any
            msg: Kafka message object
        """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    
    def send_news_message(self, message: KafkaNewsMessage, topic: Optional[str] = None) -> None:
        """Send a news message to Kafka topic.
        
        Args:
            message: News message to send
            topic: Kafka topic name. If None, uses default news topic.
        """
        topic = topic or self.topic_news
        
        try:
            # Serialize message to JSON
            message_json = message.json()
            message_bytes = message_json.encode('utf-8')
            
            # Generate key based on source and timestamp
            key = f"{message.source}_{message.timestamp.strftime('%Y%m%d_%H%M')}"
            key_bytes = key.encode('utf-8')
            
            # Send message to Kafka
            self.producer.produce(
                topic=topic,
                key=key_bytes,
                value=message_bytes,
                callback=self.delivery_callback
            )
            
            logger.info(f"Sent news message to topic '{topic}' with key '{key}'")
            
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            raise
    
    def send_raw_news_data(self, data: Dict[str, Any], source: str, 
                          country: Optional[str] = None, 
                          category: Optional[str] = None) -> None:
        """Send raw news data to Kafka topic.
        
        Args:
            data: Raw news data from API
            source: Source identifier
            country: Country code if applicable
            category: Category if applicable
        """
        try:
            # Create message with raw data
            message = KafkaNewsMessage(
                source=source,
                country=country,
                category=category,
                articles=data.get('articles', []),
                total_results=data.get('totalResults', 0)
            )
            
            # Send to raw news topic
            self.send_news_message(message, self.topic_raw_news)
            
        except Exception as e:
            logger.error(f"Failed to send raw news data: {e}")
            raise
    
    def flush(self, timeout: float = 10.0) -> None:
        """Flush all pending messages.
        
        Args:
            timeout: Maximum time to wait for messages to be delivered
        """
        try:
            remaining = self.producer.flush(timeout=timeout)
            if remaining > 0:
                logger.warning(f"{remaining} messages were not delivered within timeout")
            else:
                logger.info("All messages flushed successfully")
        except Exception as e:
            logger.error(f"Error during flush: {e}")
            raise
    
    def close(self) -> None:
        """Close the producer."""
        try:
            self.flush()
            logger.info("Kafka producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 