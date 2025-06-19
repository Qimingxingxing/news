#!/usr/bin/env python3
"""Simple test script to verify NewsAPI key works."""

import os
import sys
import requests
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_news_api_key():
    """Test the NewsAPI key with minimal requests."""
    api_key = "159a9d379deb443bb999115ecee1c441"
    base_url = "https://newsapi.org/v2"
    
    print(f"Testing NewsAPI key: {api_key[:8]}...")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 50)
    
    # Test 1: Get sources (lightweight request)
    print("Test 1: Getting news sources...")
    try:
        response = requests.get(
            f"{base_url}/sources",
            params={"apiKey": api_key},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok':
            sources_count = len(data.get('sources', []))
            print(f"✅ SUCCESS: Found {sources_count} news sources")
        else:
            print(f"❌ ERROR: {data.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Test 2: Get top headlines for US (one request)
    print("\nTest 2: Getting top headlines for US...")
    try:
        response = requests.get(
            f"{base_url}/top-headlines",
            params={
                "apiKey": api_key,
                "country": "us",
                "pageSize": 5  # Only get 5 articles to minimize data
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok':
            articles_count = len(data.get('articles', []))
            total_results = data.get('totalResults', 0)
            print(f"✅ SUCCESS: Got {articles_count} articles (total available: {total_results})")
            
            # Show first article title
            if articles_count > 0:
                first_article = data['articles'][0]
                print(f"   Sample article: {first_article.get('title', 'No title')[:60]}...")
        else:
            print(f"❌ ERROR: {data.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Your NewsAPI key is working correctly.")
    print("You can now proceed with the Docker setup.")
    return True

if __name__ == "__main__":
    success = test_news_api_key()
    sys.exit(0 if success else 1) 