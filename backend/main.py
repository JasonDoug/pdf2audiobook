import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.api.v1 import auth, jobs, payments, webhooks

# --- App Initialization ---
app = FastAPI(
    title="PDF2AudioBook API",
    description="API for converting PDF documents to audiobooks.",
    version="1.0.0"
)

# --- Middleware ---

# Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logging.info(
        f"'{request.method} {request.url.path}' {response.status_code} {process_time:.4f}s"
    )
    return response

# --- API Routers ---

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])

# --- Health Check & Root Endpoint ---

@app.get("/health", tags=["System"])
async def health_check():
    """
    Performs a health check on the API and its dependencies.
    """
    try:
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        finally:
            db.close()
    except Exception:
            db_status = "unhealthy"
    return {"status": "healthy", "dependencies": {"database": db_status}}

@app.get("/", tags=["System"])
def read_root():
    return {"message": "Welcome to the PDF2AudioBook API"}