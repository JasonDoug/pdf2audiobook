from app.core.logging import setup_logging
from loguru import logger

# --- App Initialization ---
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="API for converting PDF documents to audiobooks.",
)

# --- Middleware ---


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

    db_status = "unhealthy"

    redis_status = "unhealthy"

    s3_status = "unhealthy"

    try:
        db = SessionLocal()

        try:
            db.execute("SELECT 1")

            db_status = "healthy"

        finally:
            db.close()

    except Exception:
        pass

    try:
        redis_client = redis.from_url(settings.REDIS_URL)

        if redis_client.ping():
            redis_status = "healthy"

    except Exception:
        pass

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
        pass

    return {
        "status": "healthy",
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
            "s3": s3_status,
        },
    }


@app.get("/", tags=["System"])
def read_root():
    return {"message": "Welcome to the PDF2AudioBook API"}
