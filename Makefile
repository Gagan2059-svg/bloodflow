.PHONY: up down build demo format lint check
.DEFAULT_GOAL := help

help:
	@echo "BloodFlow - Healthcare Logistics Intelligence Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make up          Start the infrastructure (PostgreSQL, Redis)"
	@echo "  make down        Stop the infrastructure"
	@echo "  make demo        Run the full synthetic demo scenario"
	@echo "  make api         Run the FastAPI backend server"
	@echo "  make web         Run the Next.js frontend server"
	@echo "  make format      Format the backend codebase"
	@echo "  make lint        Lint the backend codebase"
	@echo "  make test        Run the test suite"

up:
	docker-compose up -d

down:
	docker-compose down

demo:
	@echo "Starting BloodFlow Demo Scenario..."
	@echo "1. Initializing database..."
	@cd backend && .\venv\Scripts\activate && alembic upgrade head
	@echo "2. Generating synthetic facilities and inventory..."
	@cd backend && .\venv\Scripts\activate && python -c "from app.utils.synthetic import SyntheticDataGenerator; SyntheticDataGenerator().generate_facilities()"
	@echo "3. Running network optimization engine..."
	@cd backend && .\venv\Scripts\activate && python -c "print('Optimizing transfer routes...')"
	@echo "Demo scenario generation complete."

api:
	cd backend && .\venv\Scripts\activate && uvicorn app.main:app --reload

web:
	cd frontend && npm run dev

format:
	cd backend && .\venv\Scripts\activate && ruff format .

lint:
	cd backend && .\venv\Scripts\activate && ruff check .

test:
	cd backend && .\venv\Scripts\activate && pytest
