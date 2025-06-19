#!/bin/bash

# Test runner script for the news polling service

set -e

echo "Running tests for News Polling Service..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install it first."
    exit 1
fi

# Install dependencies if needed
echo "Installing dependencies..."
poetry install

# Run tests
echo "Running tests..."
poetry run pytest tests/ -v

echo "Tests completed successfully!" 