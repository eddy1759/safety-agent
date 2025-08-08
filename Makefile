# .PHONY prevents conflicts with files of the same name
.PHONY: install build test run-api scan run-docker clean lint format check-deps help validate-env

# Use bash explicitly with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Configuration
IMAGE_NAME := secure-agent-toolkit
PYTHON_VERSION := 3.11
PORT := 8000
TEST_FILE := test_data/unsafe_requirements.txt

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m

# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default target
.DEFAULT_GOAL := help

## Development Commands

install: ## Install dependencies using Poetry
	@printf "$(CYAN)Installing dependencies...$(NC)\n"
	@command -v poetry >/dev/null 2>&1 || { printf "$(RED)Error: Poetry not installed. Install from https://python-poetry.org$(NC)\n" >&2; exit 1; }
	@poetry --version
	poetry install --with dev
	@printf "$(GREEN)✅ Dependencies installed successfully$(NC)\n"

validate-env: ## Validate required environment variables
	@printf "$(CYAN)Validating environment...$(NC)\n"
	@if [ -z "${GOOGLE_API_KEY:-}" ]; then \
		printf "$(YELLOW)⚠️  Warning: GOOGLE_API_KEY not set$(NC)\n"; \
	else \
		printf "$(GREEN)✅ GOOGLE_API_KEY is configured$(NC)\n"; \
	fi
	@if [ -z "${AGENT_SCAN_TIMEOUT:-}" ]; then \
		printf "$(YELLOW)⚠️  Info: AGENT_SCAN_TIMEOUT not set (using default 600s)$(NC)\n"; \
	else \
		printf "$(GREEN)✅ AGENT_SCAN_TIMEOUT is set to ${AGENT_SCAN_TIMEOUT}s$(NC)\n"; \
	fi

check-deps: ## Check for outdated dependencies
	@printf "$(CYAN)Checking for outdated dependencies...$(NC)\n"
	@poetry show --outdated || printf "$(GREEN)✅ All dependencies are up to date$(NC)\n"

## Testing Commands

test: ## Run pytest with coverage
	@printf "$(CYAN)Running tests...$(NC)\n"
	@poetry run python -c "import sys; print(f'Python version: {sys.version}')"
	@poetry run pytest -v --tb=short --cov=agent --cov-report=term-missing
	@printf "$(GREEN)✅ Tests completed$(NC)\n"

test-verbose: ## Run pytest with verbose output
	@printf "$(CYAN)Running tests with verbose output...$(NC)\n"
	@poetry run pytest -vvs --tb=long

lint: ## Run linting checks
	@printf "$(CYAN)Running linting checks...$(NC)\n"
	@poetry run ruff check agent/ || printf "$(YELLOW)⚠️  Linting issues found$(NC)\n"
	@poetry run mypy agent/ || printf "$(YELLOW)⚠️  Type checking issues found$(NC)\n"

format: ## Format code with black and ruff
	@printf "$(CYAN)Formatting code...$(NC)\n"
	@poetry run black agent/
	@poetry run ruff format agent/
	@printf "$(GREEN) Code formatted$(NC)"

## Application Commands

## Run the FastAPI server locally
run-api: validate-env
	@printf "$(CYAN)Starting FastAPI server on port $(PORT)...$(NC)\n"
	@poetry run uvicorn agent.api:app --host 0.0.0.0 --port $(PORT) --reload

## Run the FastAPI server locally
scan: validate-env
	@printf "$(CYAN)Running security scan on $(TEST_FILE)...$(NC)\n"
	@if [ ! -f "$(TEST_FILE)" ]; then \
		printf "$(RED)Error: Test file $(TEST_FILE) not found$(NC)\n" >&2; \
		exit 1; \
	fi
	@poetry run agent "$(TEST_FILE)" || { \
		printf "$(YELLOW)⚠️  Vulnerabilities found or scan failed$(NC)\n"; \
		exit 0; \
	}

 ## Run scan on custom file (usage: make scan-file FILE=path/to/requirements.txt)
scan-file: validate-env
	@printf "$(CYAN)Running security scan on $(FILE)...$(NC)\n"
	@if [ -z "$(FILE)" ]; then \
		printf "$(RED)Error: FILE parameter required. Usage: make scan-file FILE=path/to/requirements.txt$(NC)\n" >&2; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		printf "$(RED)Error: File $(FILE) not found$(NC)\n" >&2; \
		exit 1; \
	fi
	@poetry run agent "$(FILE)" || { \
		printf "$(YELLOW)⚠️  Vulnerabilities found or scan failed$(NC)\n"; \
		exit 0; \
	}

## Docker Commands

## Build Docker image
build:
	@printf "$(CYAN)Building Docker image $(IMAGE_NAME):latest...$(NC)\n"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Error: Docker not installed$(NC)" >&2; exit 1; }
	docker build -t $(IMAGE_NAME):latest .
	@printf "$(GREEN)✅ Docker image built successfully$(NC)\n"

## Build and run application in Docker
run-docker: build validate-env
	@printf "$(CYAN)Running application in Docker container...$(NC)\n"
	@docker run --rm -p $(PORT):$(PORT) \
		-e GOOGLE_API_KEY="$${GOOGLE_API_KEY:-}" \
		-e OPENAI_API_KEY="$${OPENAI_API_KEY:-}" \
		$(IMAGE_NAME):latest

## Run Docker container interactively
run-docker-interactive: build
	@printf "$(CYAN)Running Docker container interactively...$(NC)\n"
	@docker run --rm -it -p $(PORT):$(PORT) \
		-e GOOGLE_API_KEY="$${GOOGLE_API_KEY:-}" \
		-e OPENAI_API_KEY="$${OPENAI_API_KEY:-}" \
		$(IMAGE_NAME):latest /bin/bash

## Run scan inside Docker container
docker-scan: build
	@printf "$(CYAN)Running scan in Docker container...$(NC)\n"
	@docker run --rm \
		-e GOOGLE_API_KEY="$${GOOGLE_API_KEY:-}" \
		-v $$(pwd)/test_data:/app/test_data:ro \
		$(IMAGE_NAME):latest \
		python -m agent test_data/unsafe_requirements.txt


## Maintenance Commands

## Clean up temporary files and caches
clean: 
	@printf "$(CYAN)Cleaning up...$(NC)\n"
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .coverage htmlcov/ .mypy_cache/ .ruff_cache/ 2>/dev/null || true
	@printf "$(GREEN)✅ Cleanup completed$(NC)\n"

clean-docker: ## Remove Docker images and containers
	@printf "$(CYAN)Cleaning Docker resources...$(NC)\n"
	@docker rmi $(IMAGE_NAME):latest 2>/dev/null || printf "$(YELLOW)⚠️  Image not found$(NC)\n"
	@docker system prune -f
	@printf "$(GREEN)✅ Docker cleanup completed$(NC)\n"

## Security Commands

security-check: ## Run security checks on dependencies
	@printf "$(CYAN)Running security checks...$(NC)\n"
	@poetry run safety check || printf "$(YELLOW)⚠️  Security issues found$(NC)\n"
	@poetry run bandit -r agent/ || printf "$(YELLOW)⚠️  Code security issues found$(NC)\n"

update-deps: ## Update dependencies to latest versions
	@printf "$(CYAN)Updating dependencies...$(NC)\n"
	@poetry update
	@printf "$(GREEN)✅ Dependencies updated$(NC)\n"

## CI/CD Commands

## Run full CI test suite
ci-test: install lint test
	@printf "$(GREEN)✅ CI tests completed successfully$(NC)\n"

## Run CI build pipeline
ci-build: install test build
	@printf "$(GREEN)✅ CI build completed successfully$(NC)\n"

## Information Commands

info: ## Show project information
	@printf "$(CYAN)Project Information:$(NC)\n"
	@printf "  Image Name: $(IMAGE_NAME)\n"
	@printf "  Python Version: $(PYTHON_VERSION)\n"
	@printf "  Port: $(PORT)\n"
	@printf "  Test File: $(TEST_FILE)\n"
	@printf "\n$(CYAN)Environment:$(NC)\n"
	@python --version 2>/dev/null || printf "  Python: Not found\n"
	@poetry --version 2>/dev/null || printf "  Poetry: Not found\n"
	@docker --version 2>/dev/null || printf "  Docker: Not found\n"

version: ## Show version information
	@printf "$(CYAN)Version Information:$(NC)\n"
	@poetry version || printf "  Project version not found\n"

help: ## Show this help message
	@printf "\033[36mSecurity Agent Toolkit - Available Commands:\033[0m\n\n"
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":[ \t]*##[ \t]*"}; {printf "  \033[32m%-20s\033[0m %s\n", $$1, $$2}'
	@printf "\n\033[36mUsage Examples:\033[0m\n"
	@printf " 	make install 	 	 	 	# Install dependencies\n"
	@printf " 	make scan 	 	 	 	 	# Run scan on test file\n"
	@printf " 	make scan-file FILE=my.txt 	# Run scan on custom file\n"
	@printf " 	make run-api 	 	 	 	 	# Start API server\n"
	@printf " 	make test 	 	 	 	 	# Run tests\n"
	@printf " 	make build 	 	 	 	 	# Build Docker image\n"
	@printf "\n\033[36mEnvironment Setup:\033[0m\n"
	@printf " 	Create a .env file with GOOGLE_API_KEY=your_key_here\n"

# Error handling for missing targets
%:
	@printf "$(RED)Error: Unknown target '$@'$(NC)\n"
	@printf "Run 'make help' to see available commands.\n"
	@exit 1