.PHONY: help install test format lint clean build up down logs

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies with Poetry"
	@echo "  test       - Run tests"
	@echo "  format     - Format code with Black"
	@echo "  lint       - Run linting with flake8"
	@echo "  clean      - Clean up generated files"
	@echo "  build      - Build Docker image"
	@echo "  up         - Start services with Docker Compose"
	@echo "  down       - Stop services with Docker Compose"
	@echo "  logs       - View service logs"
	@echo "  setup      - Initial setup (install + create .env)"

# Install dependencies
install:
	@echo "Installing dependencies..."
	poetry install

# Run tests
test:
	@echo "Running tests..."
	poetry run pytest tests/ -v

# Format code
format:
	@echo "Formatting code..."
	poetry run black src/ tests/
	poetry run isort src/ tests/

# Run linting
lint:
	@echo "Running linting..."
	poetry run flake8 src/ tests/
	poetry run mypy src/

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf logs/*.log

# Build Docker image
build:
	@echo "Building Docker image..."
	docker-compose build

# Start services
up:
	@echo "Starting services..."
	docker-compose up -d

# Stop services
down:
	@echo "Stopping services..."
	docker-compose down

# View logs
logs:
	@echo "Viewing service logs..."
	docker-compose logs -f news-polling-service

# Initial setup
setup: install
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file. Please edit it and add your NewsAPI key."; \
	else \
		echo ".env file already exists."; \
	fi

# Run service locally (for development)
run-local:
	@echo "Running service locally..."
	poetry run python main.py

# Check service status
status:
	@echo "Checking service status..."
	docker-compose ps

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

# Remove all containers and volumes
clean-docker:
	@echo "Cleaning Docker containers and volumes..."
	docker-compose down -v
	docker system prune -f 