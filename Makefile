.PHONY: help setup install test run clean docker-up docker-down docker-build

help: ## Show this help message
	@echo "MindTrade AI - Development Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Run initial project setup
	python scripts/setup.py

install: ## Install Python dependencies
	pip install -r requirements.txt

test: ## Run tests
	pytest tests/ -v

run-api: ## Run FastAPI server locally
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard: ## Run Streamlit dashboard locally
	streamlit run ui/app.py --server.port 8501

docker-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-build: ## Build Docker images
	docker-compose build

docker-logs: ## Show Docker logs
	docker-compose logs -f

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage

format: ## Format code with black and isort
	black .
	isort .

lint: ## Run linting checks
	flake8 .
	mypy .

check: format lint test ## Run all checks (format, lint, test)

logs: ## Create logs directory
	mkdir -p logs

dev: docker-up ## Start development environment
	@echo "🚀 Development environment started!"
	@echo "📊 Dashboard: http://localhost:8501"
	@echo "🔌 API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"
