from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import ValidationError
import sys
import os

# Add parent directory to path to handle imports when run from app directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.connection import connect_to_mongo, close_mongo_connection
from app.routes import auth_routes, student_routes, faculty_routes, ai_routes, admin_routes, payment_routes
from app.middleware.rate_limiting import (
    rate_limiting_middleware,
    logging_middleware,
    validation_middleware,
    security_headers_middleware
)
from app.utils.enhanced_responses import (
    handle_app_exception,
    handle_validation_error,
    handle_http_exception,
    handle_generic_exception,
    AppException
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting StudyFriend API...")
    await connect_to_mongo()
    logger.info("✅ Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down...")
    await close_mongo_connection()
    logger.info("✅ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="StudyFriend API",
    description="A comprehensive student-faculty learning platform with AI-powered assistance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(security_headers_middleware)
app.middleware("http")(rate_limiting_middleware)
app.middleware("http")(logging_middleware)
app.middleware("http")(validation_middleware)


# Enhanced exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions"""
    return handle_app_exception(exc)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return handle_validation_error(exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return handle_http_exception(exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return handle_generic_exception(exc)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "online",
        "message": "StudyFriend API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "api_version": settings.API_VERSION
    }


# Include routers
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(student_routes.router, prefix="/api/v1")
app.include_router(faculty_routes.router, prefix="/api/v1")
app.include_router(ai_routes.router, prefix="/api/v1")
app.include_router(admin_routes.router, prefix="/api/v1")
app.include_router(payment_routes.router, prefix="/api/v1")


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
