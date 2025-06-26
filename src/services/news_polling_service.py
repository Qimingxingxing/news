"""Long-running news polling service."""

import signal
import sys
import time
from typing import Optional
import schedule
from loguru import logger

from ..config import Config
from ..models import PollingJobConfig
from ..clients import NewsAPIClient, NewsKafkaProducer, NewsRedisClient
from .article_scraper_service import ArticleScraperService


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
        self.redis_client = NewsRedisClient()
        
        # Initialize article scraper if enabled
        self.article_scraper = None
        if Config.ENABLE_ARTICLE_SCRAPING:
            self.article_scraper = ArticleScraperService(
                timeout=Config.SCRAPING_TIMEOUT,
                max_retries=Config.SCRAPING_MAX_RETRIES
            )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Initialized News Polling Service with Redis deduplication")
        if self.article_scraper:
            logger.info("Article scraping enabled")
        else:
            logger.info("Article scraping disabled")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _filter_duplicates(self, news_data: dict) -> dict:
        """Filter duplicate articles from news data using Redis.
        
        Args:
            news_data: News data dictionary from NewsAPI
            
        Returns:
            News data with duplicates filtered out
        """
        articles = news_data.get('articles', [])
        if not articles:
            return news_data
        
        # Filter duplicates
        unique_articles = self.redis_client.filter_duplicates(articles)
        
        # Update the news data with filtered articles
        filtered_data = news_data.copy()
        filtered_data['articles'] = unique_articles
        filtered_data['totalResults'] = len(unique_articles)
        
        return filtered_data
    
    def _scrape_articles(self, news_data: dict) -> dict:
        """Scrape full content for articles if scraping is enabled.
        
        Args:
            news_data: News data dictionary with articles
            
        Returns:
            News data with scraped content added to articles
        """
        if not self.article_scraper:
            return news_data
        
        articles = news_data.get('articles', [])
        if not articles:
            return news_data
        
        logger.info(f"Starting article scraping for {len(articles)} articles")
        
        # Scrape articles
        scraped_articles = self.article_scraper.scrape_articles(articles)
        
        # Update the news data with scraped articles
        scraped_data = news_data.copy()
        scraped_data['articles'] = scraped_articles
        
        return scraped_data
    
    def _poll_news(self) -> None:
        """Poll news from NewsAPI and send to Kafka."""
        try:
            logger.info("Starting news polling cycle")
            
            # Fetch news data
            news_data_list = self.news_client.get_news_for_polling(self.config)
            
            total_articles_before = 0
            total_articles_after = 0
            total_scraped = 0
            
            # Process each news dataset
            for news_data in news_data_list:
                metadata = news_data.get('_metadata', {})
                articles_before = len(news_data.get('articles', []))
                total_articles_before += articles_before
                
                # Step 1: Filter duplicates
                filtered_data = self._filter_duplicates(news_data)
                articles_after_dedup = len(filtered_data.get('articles', []))
                
                # Step 2: Scrape articles (if enabled)
                if self.article_scraper and articles_after_dedup > 0:
                    scraped_data = self._scrape_articles(filtered_data)
                    articles_with_scraped_content = sum(
                        1 for article in scraped_data.get('articles', [])
                        if article.get('scraped_content')
                    )
                    total_scraped += articles_with_scraped_content
                    final_data = scraped_data
                else:
                    final_data = filtered_data
                
                articles_after = len(final_data.get('articles', []))
                total_articles_after += articles_after
                
                # Only send to Kafka if there are unique articles
                if articles_after > 0:
                    try:
                        self.kafka_producer.send_raw_news_data(
                            data=final_data,
                            source=metadata.get('source', 'unknown'),
                            country=metadata.get('country'),
                            category=metadata.get('category')
                        )
                        
                        logger.info(f"Sent {articles_after} unique articles to Kafka: {metadata.get('country', 'unknown')} - {metadata.get('category', 'general')}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send news data to Kafka: {e}")
                else:
                    logger.info(f"No unique articles for: {metadata.get('country', 'unknown')} - {metadata.get('category', 'general')}")
            
            # Flush messages to ensure delivery
            self.kafka_producer.flush()
            
            duplicates_filtered = total_articles_before - total_articles_after
            logger.info(f"Completed news polling cycle. Processed {len(news_data_list)} datasets")
            logger.info(f"Articles: {total_articles_before} total, {total_articles_after} unique, {duplicates_filtered} duplicates filtered")
            
            if self.article_scraper and total_scraped > 0:
                logger.info(f"Article scraping: {total_scraped} articles successfully scraped")
            
            # Log Redis stats periodically
            if self.running:  # Only log stats if service is still running
                stats = self.redis_client.get_dedup_stats()
                logger.info(f"Redis dedup stats: {stats.get('total_dedup_keys', 0)} cached keys")
            
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
        
        # Log Redis configuration
        logger.info(f"Redis deduplication enabled: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        logger.info(f"Dedup TTL: {Config.REDIS_DEDUP_TTL_HOURS} hours")
        
        # Log scraping configuration
        if self.article_scraper:
            logger.info(f"Article scraping enabled: timeout={Config.SCRAPING_TIMEOUT}s, retries={Config.SCRAPING_MAX_RETRIES}")
        else:
            logger.info("Article scraping disabled")
        
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
        
        # Close Redis client
        try:
            self.redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
        
        # Close article scraper
        if self.article_scraper:
            try:
                self.article_scraper.close()
            except Exception as e:
                logger.error(f"Error closing article scraper: {e}")
        
        logger.info("News Polling Service stopped")
    
    def run_once(self) -> None:
        """Run a single polling cycle (useful for testing)."""
        logger.info("Running single news polling cycle")
        self._poll_news()
        self.kafka_producer.flush()
    
    def get_dedup_stats(self) -> dict:
        """Get deduplication statistics.
        
        Returns:
            Dictionary with deduplication statistics
        """
        return self.redis_client.get_dedup_stats()
    
    def clear_dedup_cache(self) -> bool:
        """Clear all deduplication cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        return self.redis_client.clear_dedup_cache()


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