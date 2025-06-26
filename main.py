#!/usr/bin/env python3
"""Main entry point for the news polling service."""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services import NewsPollingService

if __name__ == "__main__":
    # Import and run the main function from the service
    from src.services.news_polling_service import main
    main() 