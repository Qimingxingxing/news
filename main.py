#!/usr/bin/env python3
"""Main entry point for the news polling service."""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.news_polling_service import main

if __name__ == "__main__":
    main() 