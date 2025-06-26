# Project Structure Documentation

## 🏗️ New Package Organization

The project has been restructured to follow a more organized, service-oriented architecture with clear separation of concerns.

## 📁 Directory Structure

```
src/
├── services/           # Business logic services
│   ├── __init__.py
│   ├── news_polling_service.py      # Main news polling orchestration
│   └── article_scraper_service.py   # Article content scraping (placeholder)
├── clients/            # External API integrations
│   ├── __init__.py
│   ├── news_api_client.py           # NewsAPI HTTP client
│   └── kafka_client.py              # Kafka producer client
├── models/             # Data models and schemas
│   ├── __init__.py
│   ├── news.py                     # News-related models
│   └── kafka.py                    # Kafka message models
├── config/             # Configuration management
│   ├── __init__.py
│   └── settings.py                 # Application settings
└── utils/              # Shared utilities
    ├── __init__.py
    └── logging.py                  # Logging configuration
```

## 🔧 Package Responsibilities

### **Services** (`src/services/`)
- **Business Logic**: Core application services that orchestrate workflows
- **NewsPollingService**: Main service that coordinates news polling and Kafka publishing
- **ArticleScraperService**: Service for scraping full article content (placeholder)

### **Clients** (`src/clients/`)
- **External Integrations**: Clients for external APIs and services
- **NewsAPIClient**: HTTP client for NewsAPI integration
- **NewsKafkaProducer**: Kafka producer for message publishing

### **Models** (`src/models/`)
- **Data Structures**: Pydantic models for data validation and serialization
- **news.py**: News-related models (NewsArticle, NewsSource, etc.)
- **kafka.py**: Kafka message models (KafkaNewsMessage)

### **Config** (`src/config/`)
- **Configuration Management**: Application settings and environment variables
- **settings.py**: Centralized configuration with environment variable support

### **Utils** (`src/utils/`)
- **Shared Utilities**: Common functionality used across the application
- **logging.py**: Centralized logging configuration

## 📦 Import Patterns

### **From Services**
```python
from src.services import NewsPollingService, ArticleScraperService
```

### **From Clients**
```python
from src.clients import NewsAPIClient, NewsKafkaProducer
```

### **From Models**
```python
from src.models import NewsArticle, PollingJobConfig, KafkaNewsMessage
```

### **From Config**
```python
from src.config import Config
```

### **From Utils**
```python
from src.utils import setup_logging, get_logger
```

## 🔄 Migration Changes

### **File Moves**
- `src/news_polling_service.py` → `src/services/news_polling_service.py`
- `src/article_scraper_service.py` → `src/services/article_scraper_service.py`
- `src/news_api_client.py` → `src/clients/news_api_client.py`
- `src/kafka_producer.py` → `src/clients/kafka_client.py`
- `src/config.py` → `src/config/settings.py`
- `src/models.py` → Split into `src/models/news.py` and `src/models/kafka.py`

### **Import Updates**
All import statements have been updated to use relative imports within the new package structure:
- `from .config import Config` → `from ..config import Config`
- `from .models import ...` → `from ..models import ...`
- `from .clients import ...` → `from ..clients import ...`

## 🎯 Benefits

1. **Clear Separation**: Each package has a specific responsibility
2. **Better Organization**: Related functionality is grouped together
3. **Easier Testing**: Services and clients can be tested independently
4. **Scalability**: Easy to add new services or clients
5. **Maintainability**: Clear structure makes code easier to understand and maintain

## 🚀 Usage

The main entry point remains the same:
```bash
python main.py
```

The application will automatically use the new package structure with all the benefits of better organization. 