# News Polling Service

A long-running service that polls news data from [NewsAPI](https://newsapi.org/) and writes the results to Kafka topics. The service is designed to run continuously and can be easily deployed using Docker and Docker Compose.

## Features

- **Continuous Polling**: Automatically polls NewsAPI at configurable intervals
- **Multi-Country Support**: Fetches news from multiple countries (US, UK, Canada, Australia)
- **Category-Based Filtering**: Supports different news categories (business, technology, science, health)
- **Kafka Integration**: Writes news data to Kafka topics for downstream processing
- **Docker Support**: Fully containerized with Docker and Docker Compose
- **Poetry Dependency Management**: Modern Python dependency management
- **Comprehensive Logging**: Structured logging with loguru
- **Graceful Shutdown**: Handles shutdown signals properly
- **Health Checks**: Built-in health monitoring

## Architecture

The service consists of several components:

1. **NewsAPI Client**: Fetches news data from NewsAPI
2. **Kafka Producer**: Writes news data to Kafka topics
3. **Polling Service**: Orchestrates the polling process
4. **Configuration Management**: Handles environment variables and settings

### Kafka Topics

- `raw-news`: Raw news data from NewsAPI
- `news-articles`: Processed news articles (for future use)

## Prerequisites

- Docker and Docker Compose
- NewsAPI key (get one from [https://newsapi.org/](https://newsapi.org/))

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd news
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your NewsAPI key
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

4. **Monitor the logs**:
   ```bash
   docker-compose logs -f news-polling-service
   ```

5. **Access Kafka UI** (optional):
   - Open http://localhost:8080 in your browser
   - Monitor topics and messages

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEWS_API_KEY` | Your NewsAPI key (required) | - |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | `localhost:9092` |
| `KAFKA_TOPIC_NEWS` | Topic for processed news | `news-articles` |
| `KAFKA_TOPIC_RAW_NEWS` | Topic for raw news data | `raw-news` |
| `POLLING_INTERVAL_MINUTES` | Polling interval in minutes | `15` |
| `MAX_ARTICLES_PER_REQUEST` | Max articles per API request | `100` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Polling Configuration

The service polls news for the following countries and categories:

**Countries**: US, UK, Canada, Australia
**Categories**: Business, Technology, Science, Health

You can modify these in the `PollingJobConfig` class in `src/models.py`.

## Development

### Local Development Setup

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment**:
   ```bash
   cp env.example .env
   # Add your NewsAPI key to .env
   ```

4. **Run the service locally**:
   ```bash
   poetry run python main.py
   ```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
poetry run flake8 src/
```

## Docker Services

The Docker Compose setup includes:

- **Zookeeper**: Required for Kafka
- **Kafka**: Message broker
- **Kafka UI**: Web interface for monitoring Kafka
- **News Polling Service**: The main application
- **Kafka Topics Creator**: Creates required topics on startup

## Monitoring

### Logs

Service logs are available in the `logs/` directory and can be viewed with:

```bash
docker-compose logs -f news-polling-service
```

### Kafka UI

Access the Kafka UI at http://localhost:8080 to:
- Monitor topics and partitions
- View message contents
- Check consumer groups

### Health Checks

The service includes health checks that can be monitored:

```bash
docker-compose ps
```

## Data Flow

1. **Polling Trigger**: Service polls NewsAPI every 15 minutes (configurable)
2. **Data Fetching**: Fetches news for each country and category combination
3. **Kafka Publishing**: Sends raw news data to `raw-news` topic
4. **Message Structure**: Each message contains metadata and article data

### Message Format

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "source": "top_headlines",
  "country": "us",
  "category": "technology",
  "articles": [...],
  "total_results": 100
}
```

## Future Enhancements

- **Article Scraping Service**: A separate service to read from `raw-news` topic and scrape full article content
- **Data Processing Pipeline**: Stream processing with Kafka Streams
- **Metrics and Monitoring**: Prometheus metrics and Grafana dashboards
- **Schema Registry**: Avro schemas for data validation
- **Error Handling**: Dead letter queues for failed messages
- **Rate Limiting**: More sophisticated rate limiting for NewsAPI

## Troubleshooting

### Common Issues

1. **NewsAPI Key Missing**:
   ```
   ValueError: NEWS_API_KEY environment variable is required
   ```
   Solution: Add your NewsAPI key to the `.env` file

2. **Kafka Connection Failed**:
   ```
   Failed to connect to Kafka
   ```
   Solution: Ensure Kafka is running and accessible

3. **Rate Limiting**:
   ```
   NewsAPI error: rateLimited
   ```
   Solution: The service includes delays between requests, but you may need to adjust the polling interval

### Debug Mode

To run in debug mode, set `LOG_LEVEL=DEBUG` in your `.env` file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review the logs
- Open an issue on GitHub
