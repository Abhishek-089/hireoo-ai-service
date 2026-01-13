"""
Hireoo AI Extraction Service
FastAPI microservice for extracting job information from LinkedIn posts using AI.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from contextlib import asynccontextmanager

from app.api import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.extraction_service import ExtractionService

# Setup logging
setup_logging()

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting Hireoo AI Extraction Service")

    # Initialize services
    extraction_service = ExtractionService()
    await extraction_service.initialize()

    # Store service instance
    app.state.extraction_service = extraction_service

    logger.info("AI Extraction Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AI Extraction Service")
    await extraction_service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Hireoo AI Extraction Service",
    description="AI-powered job information extraction from LinkedIn posts",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hireoo-ai-extraction"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Hireoo AI Extraction Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

