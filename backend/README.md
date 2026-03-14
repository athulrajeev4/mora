# Mora Backend

Voice AI Testing & Evaluation Platform - Backend API

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (via Docker)

### 2. Setup

```bash
# Clone and navigate to backend directory
cd backend

# Copy environment file
cp .env.example .env

# Update .env with your credentials (Twilio, LiveKit, LLM API keys)

# Start PostgreSQL
cd ..
docker-compose up -d

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 3. Run the Server

```bash
# Development mode with auto-reload
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "timestamp": "2026-01-04T..."
# }
```

## API Documentation

Once the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── database.py      # DB connection
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── services/            # Business logic
│   ├── agents/              # LiveKit voice agents
│   └── integrations/        # External services
├── alembic/                 # Database migrations
├── tests/                   # Unit & integration tests
└── requirements.txt         # Python dependencies
```

## Stage 1 Completed ✅

- [x] Project structure created
- [x] PostgreSQL with Docker
- [x] SQLAlchemy models defined
- [x] Pydantic schemas created
- [x] Alembic migrations configured
- [x] FastAPI app with health check
- [x] Environment configuration

## Next Steps

Stage 2: Test Suite Management API
- Implement CRUD endpoints for test suites
- Add test case management
- Create service layer
