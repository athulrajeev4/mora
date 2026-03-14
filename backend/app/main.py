"""
Mora Backend - FastAPI Application
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db, engine, Base
from app.schemas import HealthResponse

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Mora API",
    description="Voice AI Testing & Evaluation Platform",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Mora API - Voice AI Testing Platform",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Verifies:
    - API is running
    - Database connection is active
    """
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.utcnow()
    )


# Import and include routers
from app.api.routes import test_suites, projects, webhooks, evaluations

app.include_router(test_suites.router, prefix="/api/test-suites", tags=["Test Suites"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(webhooks.router, prefix="/api/webhooks/twilio", tags=["Twilio Webhooks"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
