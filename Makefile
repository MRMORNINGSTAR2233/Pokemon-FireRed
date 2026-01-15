.PHONY: install dev backend frontend clean help

# Default target
help:
	@echo "AI Pokemon Player - Available commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make dev        - Start development servers"
	@echo "  make backend    - Start backend only"
	@echo "  make frontend   - Start frontend only"
	@echo "  make clean      - Clean up generated files"

# Install all dependencies
install: install-backend install-frontend

install-backend:
	cd backend && python -m venv venv && \
		. venv/bin/activate && \
		pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# Development servers
dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@make -j2 backend frontend

backend:
	cd backend && . venv/bin/activate && \
		uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# Clean up
clean:
	rm -rf backend/venv
	rm -rf backend/__pycache__
	rm -rf backend/**/__pycache__
	rm -rf frontend/node_modules
	rm -rf frontend/.next
	rm -rf data/screenshots/*
	rm -rf data/logs/*

# Build for production
build-frontend:
	cd frontend && npm run build

# Linting
lint:
	cd frontend && npm run lint
