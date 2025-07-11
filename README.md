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

## End-to-End Mock Data Flow (E2E)

This project supports a full mock data flow for local development and testing. The process is as follows:

1. **Mock Data Generation**: News Polling Service generates unique mock articles for each country/category.
2. **Kafka Message Flow**: Polling Service publishes articles to the `raw-news` Kafka topic.
3. **Storage Service Consumption**: News Storage Service consumes messages from `raw-news` and writes articles to MongoDB (`news_db.articles`).
4. **MongoDB Storage**: Articles are indexed and deduplicated in MongoDB.

### How to Verify the Data Flow

1. **Start All Services**
   ```sh
   docker compose up -d --build
   ```
2. **Check Polling Service Logs**
   ```sh
   docker compose logs --tail=30 news-polling-service
   ```
   You should see logs like `Sent 3 unique articles to Kafka: ...`.
3. **Check Storage Service Logs**
   ```sh
   docker compose logs --tail=30 news-storage-service
   ```
   You should see logs like `Stored news batch: ...`.
4. **Check MongoDB for Articles**
   ```sh
   docker compose exec mongodb mongosh news_db --eval "db.articles.find().limit(3).pretty()"
   ```
   You should see mock articles with fields like `title`, `content`, `category`, etc.

### Troubleshooting

- **Kafka Consumer Not Receiving Messages**: Ensure storage service subscribes to the correct topic (`raw-news`).
- **No Data in MongoDB**: Reset the Kafka consumer group offset to earliest:
  1. Stop storage service:
     ```sh
     docker compose stop news-storage-service
     ```
  2. Reset offset:
     ```sh
     docker compose exec kafka kafka-consumer-groups --bootstrap-server kafka:29092 --group news_storage_group --topic raw-news --reset-offsets --to-earliest --execute
     ```
  3. Restart storage service:
     ```sh
     docker compose up -d news-storage-service
     ```
- **ImportError/Config Errors**: Make sure all imports use the correct relative path, e.g. `from ..config.settings import Config`.
- **Kafka Console Consumer** (for debugging):
  ```sh
  docker compose exec kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic raw-news --from-beginning --max-messages 1
  ```

---

For more details, see the code comments and troubleshooting steps above. If you encounter issues, check the logs for both polling and storage services first.
