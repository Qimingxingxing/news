"""Article scraping service for extracting full content from news URLs."""

import time
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article as NewspaperArticle
from loguru import logger

from ..config import Config


class ArticleScraperService:
    """Service to scrape full article content from news URLs."""
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """Initialize the article scraper service.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set up session headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        logger.info("Article Scraper Service initialized")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted patterns
        text = re.sub(r'Advertisement|Advertise|Subscribe|Sign up|Follow us', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _scrape_with_trafilatura(self, url: str, html_content: str) -> Optional[Dict[str, Any]]:
        """Scrape article using trafilatura library.
        
        Args:
            url: Article URL
            html_content: HTML content of the page
            
        Returns:
            Scraped article data or None if failed
        """
        try:
            # Extract content using trafilatura
            extracted = trafilatura.extract(html_content, include_formatting=True, include_links=True)
            
            if not extracted:
                return None
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(html_content)
            
            return {
                "url": url,
                "title": metadata.title if metadata and metadata.title else "",
                "content": self._clean_text(extracted),
                "author": metadata.author if metadata and metadata.author else "",
                "published_date": metadata.date if metadata and metadata.date else None,
                "scraped_at": time.time(),
                "scraper": "trafilatura"
            }
            
        except Exception as e:
            logger.debug(f"Trafilatura scraping failed for {url}: {e}")
            return None
    
    def _scrape_with_newspaper3k(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape article using newspaper3k library.
        
        Args:
            url: Article URL
            
        Returns:
            Scraped article data or None if failed
        """
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()
            article.nlp()  # Extract keywords and summary
            
            if not article.text:
                return None
            
            return {
                "url": url,
                "title": article.title or "",
                "content": self._clean_text(article.text),
                "author": ", ".join(article.authors) if article.authors else "",
                "published_date": article.publish_date.isoformat() if article.publish_date else None,
                "summary": article.summary,
                "keywords": article.keywords,
                "scraped_at": time.time(),
                "scraper": "newspaper3k"
            }
            
        except Exception as e:
            logger.debug(f"Newspaper3k scraping failed for {url}: {e}")
            return None
    
    def _scrape_with_beautifulsoup(self, url: str, html_content: str) -> Optional[Dict[str, Any]]:
        """Scrape article using BeautifulSoup as fallback.
        
        Args:
            url: Article URL
            html_content: HTML content of the page
            
        Returns:
            Scraped article data or None if failed
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Try to find title
            title = ""
            title_tag = soup.find('title') or soup.find('h1') or soup.find('h2')
            if title_tag:
                title = self._clean_text(title_tag.get_text())
            
            # Try to find main content
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = self._clean_text(content_elem.get_text())
                    break
            
            # If no specific content found, get body text
            if not content:
                content = self._clean_text(soup.get_text())
            
            if not content:
                return None
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "author": "",
                "published_date": None,
                "scraped_at": time.time(),
                "scraper": "beautifulsoup"
            }
            
        except Exception as e:
            logger.debug(f"BeautifulSoup scraping failed for {url}: {e}")
            return None
    
    def scrape_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape article content from a URL using multiple methods.
        
        Args:
            url: Article URL to scrape
            
        Returns:
            Scraped article data or None if failed
        """
        if not self._is_valid_url(url):
            logger.warning(f"Invalid URL: {url}")
            return None
        
        logger.debug(f"Scraping article: {url}")
        
        # Try to fetch the HTML content
        html_content = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                html_content = response.text
                break
            except requests.RequestException as e:
                logger.debug(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # Brief delay before retry
                continue
        
        if not html_content:
            logger.warning(f"Failed to fetch content from {url}")
            return None
        
        # Try different scraping methods in order of preference
        scraped_data = None
        
        # Method 1: Try trafilatura (best for article extraction)
        if html_content:
            scraped_data = self._scrape_with_trafilatura(url, html_content)
        
        # Method 2: Try newspaper3k (good for news sites)
        if not scraped_data or not scraped_data.get('content'):
            scraped_data = self._scrape_with_newspaper3k(url)
        
        # Method 3: Fallback to BeautifulSoup
        if not scraped_data or not scraped_data.get('content'):
            scraped_data = self._scrape_with_beautifulsoup(url, html_content)
        
        if scraped_data and scraped_data.get('content'):
            logger.info(f"Successfully scraped article from {url} using {scraped_data.get('scraper', 'unknown')}")
            return scraped_data
        else:
            logger.warning(f"Failed to extract content from {url}")
            return None
    
    def scrape_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape multiple articles and add scraped content.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of articles with scraped content added
        """
        if not articles:
            return []
        
        scraped_articles = []
        successful_scrapes = 0
        failed_scrapes = 0
        
        for article in articles:
            url = article.get('url')
            if not url:
                logger.warning(f"Article missing URL: {article.get('title', 'Unknown')}")
                scraped_articles.append(article)
                continue
            
            try:
                scraped_data = self.scrape_article(url)
                if scraped_data:
                    # Merge scraped data with original article
                    enhanced_article = article.copy()
                    enhanced_article['scraped_content'] = scraped_data
                    scraped_articles.append(enhanced_article)
                    successful_scrapes += 1
                else:
                    scraped_articles.append(article)
                    failed_scrapes += 1
                
                # Rate limiting - be respectful to websites
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error scraping article {url}: {e}")
                scraped_articles.append(article)
                failed_scrapes += 1
        
        logger.info(f"Article scraping completed: {successful_scrapes} successful, {failed_scrapes} failed")
        return scraped_articles
    
    def close(self) -> None:
        """Close the scraper service and clean up resources."""
        try:
            self.session.close()
            logger.info("Article Scraper Service closed")
        except Exception as e:
            logger.error(f"Error closing scraper service: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 
