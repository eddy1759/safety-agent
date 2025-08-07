# .PHONY prevents conflicts with files of the same name.
.PHONY: install build test run-api scan run-docker

# Use bash explicitly
SHELL := /bin/bash
IMAGE_NAME := secure-agent-toolkit

# Load environment variables from .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Install dependencies using Poetry
install:
	poetry install --with dev

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME):latest .

# Run pytest inside Poetry environment
test:
	poetry run pytest

# Run the FastAPI server locally via Poetry
run-api:
	poetry run uvicorn agent.api:app --host 0.0.0.0 --port 8000 --reload

# Run a CLI scan on the unsafe requirements file
scan:
	poetry run agent scan test_data/unsafe_requirements.txt

# Build and run the entire application inside Docker
run-docker: build
	docker run --rm -p 8000:8000 -e OPENAI_API_KEY="$$OPENAI_API_KEY" $(IMAGE_NAME):latest

help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo "Use 'make <target>' to execute a command."
	@echo "For example, 'make install' to install dependencies."



