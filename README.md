# News Pipeline Service

This service is responsible for collecting news articles from various sources and storing them in a MongoDB database. It consists of two main components:

1. News Polling Service: Polls news from external APIs and writes to Kafka
2. News Storage Service: Reads news from Kafka and stores in MongoDB

## Architecture

- Kafka for message queue
- MongoDB for article storage
- Redis for deduplication
- Python with Poetry for dependency management

## Setup

1. Install Docker and Docker Compose
2. Copy `env.example` to `.env` and fill in required values
3. Run `docker-compose up -d` to start all services

## Components

### News Polling Service

- Polls news from configured sources
- Processes and validates articles
- Writes to Kafka topics

### News Storage Service

- Consumes articles from Kafka
- Stores in MongoDB with proper indexing
- Handles deduplication and updates
