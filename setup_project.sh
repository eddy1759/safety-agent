#!/bin/bash

set -e

echo "================================================================"
echo "Setting up Python Safety Agent Project"
echo "================================================================"

poetry init --name "safety-agent-app" --description "Python Safety Agent Project" --author "Eddy <eddy1759@gmail.com>" --python "^3.11" --dependency fastapi --dependency uvicorn --dependency requests --dependency typer --dev-dependency pytest --dev-dependency safety --dev-dependency coverage --no-interaction

echo "🔧 Creating project structure..."
echo "================================================================"
echo "creating directories"
echo "================================================================"
mkdir -p \
  .devcontainer \
  .github/workflows \
  agent \
  test_data \
  tests

# Create files
echo "================================================================"
echo "creating files"
echo "================================================================"
touch \
  .devcontainer/devcontainer.json \
  .github/workflows/ci.yml \
  agent/__init__.py \
  agent/api.py \
  agent/cli.py \
  agent/core.py \
  test_data/safe_requirements.txt \
  test_data/unsafe_requirements.txt \
  tests/test_agent.py \
  .env.example \
  .gitignore \
  Dockerfile \
  Makefile \
  README.md

echo "================================================================"
echo "setting up gitignore"
echo "================================================================"
echo -e ".env\n__pycache__/\n*.pyc\n*.pyo\n*.pyd\n*.db\n*.sqlite3\n*.log\n.DS_Store" > .gitignore  
echo "✅ Project structure created successfully."

echo "================================================================"
echo "Installing dependencies..."
echo "================================================================"
poetry install

echo "================================================================"
echo "✅ Project setup complete!"
