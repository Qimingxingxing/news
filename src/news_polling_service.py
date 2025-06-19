"""Long-running news polling service."""

import signal
import sys
import time
from typing import Optional
import schedule
from loguru import logger

from .config import Config
from .models import PollingJobConfig
from .news_api_client import NewsAPIClient
from .kafka_producer import NewsKafkaProducer


class NewsPollingService:
    """Long-running service that polls news from NewsAPI and sends to Kafka."""
    
    def __init__(self, config: Optional[PollingJobConfig] = None):
        """Initialize the news polling service.
        
        Args:
            config: Polling configuration. If None, uses default config.
        """
        self.config = config or PollingJobConfig()
        self.running = False
        
        # Initialize components
        self.news_client = NewsAPIClient()
        self.kafka_producer = NewsKafkaProducer()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Initialized News Polling Service")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _poll_news(self) -> None:
        """Poll news from NewsAPI and send to Kafka."""
        try:
            logger.info("Starting news polling cycle")
            
            # Fetch news data
            news_data_list = self.news_client.get_news_for_polling(self.config)
            
            # Send each news dataset to Kafka
            for news_data in news_data_list:
                metadata = news_data.get('_metadata', {})
                
                try:
                    self.kafka_producer.send_raw_news_data(
                        data=news_data,
                        source=metadata.get('source', 'unknown'),
                        country=metadata.get('country'),
                        category=metadata.get('category')
                    )
                    
                    logger.info(f"Sent news data to Kafka: {metadata.get('country', 'unknown')} - {metadata.get('category', 'general')}")
                    
                except Exception as e:
                    logger.error(f"Failed to send news data to Kafka: {e}")
            
            # Flush messages to ensure delivery
            self.kafka_producer.flush()
            
            logger.info(f"Completed news polling cycle. Processed {len(news_data_list)} datasets")
            
        except Exception as e:
            logger.error(f"Error during news polling: {e}")
    
    def start(self) -> None:
        """Start the polling service."""
        if self.running:
            logger.warning("Service is already running")
            return
        
        # Validate configuration
        Config.validate()
        
        logger.info("Starting News Polling Service")
        logger.info(f"Polling interval: {self.config.interval_minutes} minutes")
        logger.info(f"Countries: {self.config.countries}")
        logger.info(f"Categories: {self.config.categories}")
        
        self.running = True
        
        # Schedule the polling job
        schedule.every(self.config.interval_minutes).minutes.do(self._poll_news)
        
        # Run initial poll immediately
        logger.info("Running initial news poll...")
        self._poll_news()
        
        # Main loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the polling service."""
        if not self.running:
            return
        
        logger.info("Stopping News Polling Service")
        self.running = False
        
        # Close Kafka producer
        try:
            self.kafka_producer.close()
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")
        
        logger.info("News Polling Service stopped")
    
    def run_once(self) -> None:
        """Run a single polling cycle (useful for testing)."""
        logger.info("Running single news polling cycle")
        self._poll_news()
        self.kafka_producer.flush()


def main():
    """Main entry point for the news polling service."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL,
        colorize=True
    )
    logger.add(
        "logs/news_polling.log",
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL,
        rotation="1 day",
        retention="7 days"
    )
    
    try:
        # Create and start the service
        service = NewsPollingService()
        service.start()
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 