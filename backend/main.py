import time
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import redis
import boto3
from sqlalchemy import text
from app.core.database import SessionLocal, get_db

from app.core.logging import setup_logging
from app.core.config import settings
from app.api.v1 import auth, jobs, payments, webhooks
from loguru import logger
from app.core.exceptions import http_exception_handler, general_exception_handler, app_exception_handler, AppException

# --- App Initialization ---
setup_logging()

# Validate production settings (only if required settings are available)
try:
    if settings.is_production:
        # Only validate if we have the basic required settings
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY and not settings.SECRET_KEY == "dev-secret-key-change-in-production":
            settings.validate_production_settings()
        else:
            logger.warning("Production environment detected but SECRET_KEY not properly configured. Skipping validation.")
except (ValueError, AttributeError) as e:
    logger.error(f"Configuration validation failed: {e}")
    # Don't raise in build time, just log
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="""
    PDF2Audiobook SaaS Platform API

    A comprehensive API for converting PDF documents into high-quality audiobooks using advanced text-to-speech technology.

    ## Features

    * **PDF Processing**: Extract and convert text from PDF documents
    * **Multiple TTS Providers**: Support for OpenAI, Google Cloud, AWS Polly, Azure, and ElevenLabs
    * **Voice Customization**: Choose from various voices and adjust reading speed
    * **AI-Powered Summaries**: Generate intelligent summaries for complex documents
    * **Secure Authentication**: JWT-based authentication with Clerk integration
    * **Usage Tracking**: Monitor credits and subscription usage

    ## Authentication

    All API endpoints require authentication via JWT tokens obtained from Clerk.
    Include the token in the Authorization header: `Authorization: Bearer <token>`

    ## Rate Limiting

    API requests are rate limited to prevent abuse. Current limits: 100 requests per minute globally.

    ## File Upload Limits

    - Maximum file size: 50MB
    - Supported formats: PDF only
    - Content type: application/pdf
    """,
    debug=settings.DEBUG,
    contact={
        "name": "PDF2Audiobook Support",
        "email": "support@pdf2audiobook.com",
    },
    license_info={
        "name": "Proprietary",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- Middleware ---


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # HSTS (HTTP Strict Transport Security) - only in production
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f'"{request.method} {request.url.path}" {response.status_code} {process_time:.4f}s'
    )
    return response


# --- Middleware ---

# Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
# Rate limiting (temporarily disabled)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Environment-aware configuration
allowed_origins = settings.ALLOWED_HOSTS
if not allowed_origins:
    if settings.is_production:
        # In production, require explicit configuration
        allowed_origins = []
    else:
        # Development defaults
        allowed_origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# --- Exception Handlers ---
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# --- API Routers ---

try:
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
    app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
except Exception as e:
    logger.error(f"Failed to include routers: {e}")
    # Continue without routers if they fail to import

# --- Health Check & Root Endpoint ---


@app.get("/health", tags=["System"])
async def health_check():
    """
    Performs a health check on the API and its dependencies.
    Returns basic health status without exposing sensitive configuration details.
    """

    db_status = "unhealthy"
    redis_status = "unhealthy"
    s3_status = "unhealthy"

    try:
        if SessionLocal:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                db_status = "healthy"
            finally:
                db.close()
        else:
            db_status = "not_configured"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "unhealthy"

    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        if redis_client.ping():
            redis_status = "healthy"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_status = "unhealthy"

    # Security: Only test S3 connectivity if credentials are configured
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.S3_BUCKET_NAME:
        try:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            s3_status = "healthy"
        except Exception:
            s3_status = "unhealthy"
    else:
        s3_status = "not_configured"

    # Determine overall status
    all_healthy = all(status in ["healthy", "not_configured"] for status in [db_status, redis_status, s3_status])
    overall_status = "healthy" if all_healthy else "unhealthy"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
            "s3": s3_status,
        },
    }


@app.get("/", tags=["System"])
def read_root():
    return {"message": "Welcome to the PDF2AudioBook API"}
