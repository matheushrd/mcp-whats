.PHONY: help install setup-db build-images generate-manifests deploy clean test

# Default target
help:
	@echo "MCP Platform - Development Commands"
	@echo "=================================="
	@echo "make install          - Install all dependencies"
	@echo "make setup-db         - Setup PostgreSQL and Redis in K8s"
	@echo "make build-images     - Build Docker images"
	@echo "make generate-manifests - Generate K8s manifests from config"
	@echo "make deploy           - Deploy all manifests to K8s"
	@echo "make clean            - Clean generated files"
	@echo "make test             - Run tests"
	@echo "make onboard-client   - Run client onboarding script"

# Install dependencies
install:
	pip install -r orchestrator/requirements.txt
	pip install -r scripts/requirements.txt
	cd mcp-server && pip install -r requirements.txt

# Setup database
setup-db:
	kubectl create namespace mcp-platform --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f database/k8s-manifests/

# Build Docker images
build-images:
	docker build -t mcp-server:latest mcp-server/
	docker build -t mcp-web-ui:latest web-ui/

# Generate manifests
generate-manifests:
	python orchestrator/orchestrator.py

# Deploy to Kubernetes
deploy: generate-manifests
	cd generated-manifests && ./apply-all.sh

# Clean generated files
clean:
	rm -rf generated-manifests/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run tests
test:
	cd mcp-server && pytest tests/

# Onboard new client
onboard-client:
	python scripts/onboarding.py

# Development server
dev-server:
	cd mcp-server && uvicorn app.main:app --reload --port 8000

# Format code
format:
	black mcp-server/
	black orchestrator/
	black scripts/

# Lint code
lint:
	flake8 mcp-server/
	flake8 orchestrator/
	flake8 scripts/