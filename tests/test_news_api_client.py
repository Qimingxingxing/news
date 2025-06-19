"""Tests for the NewsAPI client."""

import pytest
from unittest.mock import Mock, patch
from src.news_api_client import NewsAPIClient
from src.models import PollingJobConfig


class TestNewsAPIClient:
    """Test cases for NewsAPIClient."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        api_key = "test_api_key"
        client = NewsAPIClient(api_key)
        assert client.api_key == api_key
    
    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises error."""
        with pytest.raises(ValueError, match="NewsAPI key is required"):
            NewsAPIClient("")
    
    @patch('src.news_api_client.requests.get')
    def test_get_top_headlines_success(self, mock_get):
        """Test successful top headlines request."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {
                    'source': {'id': 'test', 'name': 'Test Source'},
                    'author': 'Test Author',
                    'title': 'Test Title',
                    'description': 'Test Description',
                    'url': 'https://test.com',
                    'urlToImage': 'https://test.com/image.jpg',
                    'publishedAt': '2024-01-01T12:00:00Z',
                    'content': 'Test content'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        client = NewsAPIClient("test_key")
        result = client.get_top_headlines(country="us", category="technology")
        
        # Assertions
        assert result['status'] == 'ok'
        assert result['totalResults'] == 2
        assert len(result['articles']) == 1
        assert result['articles'][0]['title'] == 'Test Title'
    
    @patch('src.news_api_client.requests.get')
    def test_get_top_headlines_api_error(self, mock_get):
        """Test API error handling."""
        # Mock response with error
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'error',
            'message': 'API key is invalid'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        client = NewsAPIClient("test_key")
        with pytest.raises(Exception, match="NewsAPI error: API key is invalid"):
            client.get_top_headlines(country="us")
    
    def test_get_news_for_polling(self):
        """Test getting news for polling configuration."""
        config = PollingJobConfig(
            countries=["us"],
            categories=["technology"],
            interval_minutes=15,
            max_articles=10
        )
        
        with patch.object(NewsAPIClient, 'get_top_headlines') as mock_get_headlines:
            mock_get_headlines.return_value = {
                'status': 'ok',
                'totalResults': 1,
                'articles': []
            }
            
            client = NewsAPIClient("test_key")
            result = client.get_news_for_polling(config)
            
            # Should have 2 results: general headlines + technology headlines
            assert len(result) == 2
            assert all('_metadata' in item for item in result) 