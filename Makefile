.PHONY: help setup setup-uv install test test-cov format lint type-check clean docker-build docker-up docker-down docker-chat docker-models

# Default target
help:
	@echo "🛠️  Hrisa Code - Available Commands"
	@echo ""
	@echo "Local Development:"
	@echo "  make setup          - Set up venv and install dependencies"
	@echo "  make setup-uv       - Set up with uv (faster)"
	@echo "  make install        - Install package in dev mode"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage"
	@echo "  make format         - Format code with black"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make type-check     - Type check with mypy"
	@echo "  make clean          - Clean cache files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-up      - Start services (Ollama)"
	@echo "  make docker-down    - Stop services"
	@echo "  make docker-chat    - Start interactive chat"
	@echo "  make docker-models  - List available models"
	@echo "  make docker-pull    - Pull models (MODEL=codellama)"
	@echo "  make docker-clean   - Remove all containers and volumes"
	@echo ""

# Local development setup
setup:
	@./scripts/setup-venv.sh

setup-uv:
	@./scripts/setup-uv.sh

install:
	pip install -e ".[dev]"

# Testing
test:
	pytest -v

test-cov:
	pytest --cov=hrisa_code --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "📊 Coverage report: htmlcov/index.html"

# Code quality
format:
	black src/ tests/

lint:
	ruff check src/ tests/

type-check:
	mypy src/

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage dist/ build/

# Docker commands
docker-build:
	docker compose build

docker-up:
	@./scripts/docker-start.sh

docker-down:
	docker compose down

docker-chat:
	@./scripts/docker-chat.sh $(MODEL)

docker-models:
	@./scripts/docker-models.sh

docker-pull:
	@./scripts/docker-pull-models.sh $(MODEL)

docker-clean:
	@./scripts/docker-clean.sh

# Run all checks (CI-like)
check: format lint type-check test
	@echo "✅ All checks passed!"
