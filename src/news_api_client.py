"""NewsAPI client for fetching news data."""

import time
from typing import Dict, Any, List, Optional
import requests
from loguru import logger

from .config import Config
from .models import NewsAPIResponse, PollingJobConfig


class NewsAPIClient:
    """Client for interacting with NewsAPI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the NewsAPI client.
        
        Args:
            api_key: NewsAPI key. If None, uses config value.
        """
        self.api_key = api_key or Config.NEWS_API_KEY
        self.base_url = Config.NEWS_API_BASE_URL
        self.endpoints = Config.NEWS_API_ENDPOINTS
        
        if not self.api_key:
            raise ValueError("NewsAPI key is required")
        
        logger.info("Initialized NewsAPI client")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to NewsAPI.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        params['apiKey'] = self.api_key
        
        try:
            logger.debug(f"Making request to {url} with params: {params}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'error':
                error_message = data.get('message', 'Unknown error')
                logger.error(f"NewsAPI error: {error_message}")
                raise requests.RequestException(f"NewsAPI error: {error_message}")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_top_headlines(self, country: str = "us", category: Optional[str] = None, 
                         page_size: int = 100) -> Dict[str, Any]:
        """Get top headlines for a country and optional category.
        
        Args:
            country: Country code (e.g., 'us', 'gb')
            category: News category (e.g., 'business', 'technology')
            page_size: Number of articles to return (max 100)
            
        Returns:
            NewsAPI response data
        """
        params = {
            'country': country,
            'pageSize': min(page_size, 100)
        }
        
        if category:
            params['category'] = category
        
        return self._make_request(self.endpoints['top_headlines'], params)
    
    def get_everything(self, query: str, language: str = "en", 
                      sort_by: str = "publishedAt", page_size: int = 100) -> Dict[str, Any]:
        """Search for articles with a query.
        
        Args:
            query: Search query
            language: Language code (e.g., 'en')
            sort_by: Sort method ('relevancy', 'popularity', 'publishedAt')
            page_size: Number of articles to return (max 100)
            
        Returns:
            NewsAPI response data
        """
        params = {
            'q': query,
            'language': language,
            'sortBy': sort_by,
            'pageSize': min(page_size, 100)
        }
        
        return self._make_request(self.endpoints['everything'], params)
    
    def get_sources(self, category: Optional[str] = None, 
                   language: Optional[str] = None, 
                   country: Optional[str] = None) -> Dict[str, Any]:
        """Get available news sources.
        
        Args:
            category: Filter by category
            language: Filter by language
            country: Filter by country
            
        Returns:
            NewsAPI response data
        """
        params = {}
        
        if category:
            params['category'] = category
        if language:
            params['language'] = language
        if country:
            params['country'] = country
        
        return self._make_request(self.endpoints['sources'], params)
    
    def get_news_for_polling(self, config: PollingJobConfig) -> List[Dict[str, Any]]:
        """Get news data for all configured countries and categories.
        
        Args:
            config: Polling configuration
            
        Returns:
            List of news data dictionaries
        """
        news_data = []
        
        for country in config.countries:
            # Get general headlines for the country
            try:
                general_news = self.get_top_headlines(
                    country=country,
                    page_size=config.max_articles
                )
                general_news['_metadata'] = {
                    'source': 'top_headlines',
                    'country': country,
                    'category': None
                }
                news_data.append(general_news)
                logger.info(f"Fetched {general_news.get('totalResults', 0)} general headlines for {country}")
                
            except Exception as e:
                logger.error(f"Failed to fetch general headlines for {country}: {e}")
            
            # Get category-specific headlines
            for category in config.categories:
                try:
                    category_news = self.get_top_headlines(
                        country=country,
                        category=category,
                        page_size=config.max_articles
                    )
                    category_news['_metadata'] = {
                        'source': 'top_headlines',
                        'country': country,
                        'category': category
                    }
                    news_data.append(category_news)
                    logger.info(f"Fetched {category_news.get('totalResults', 0)} {category} headlines for {country}")
                    
                    # Add delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to fetch {category} headlines for {country}: {e}")
        
        return news_data 