from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Core Project Settings
    PROJECT_NAME: str = "pdf2audiobook"
    PROJECT_VERSION: str = "0.1.0"

    # Debugging
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000"]

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str

    # Authentication (Clerk)
    CLERK_PEM_PUBLIC_KEY: Optional[str] = None
    CLERK_JWT_ISSUER: Optional[str] = (
        None  # e.g., "https://clerk.your-clerk-domain.com"
    )
    CLERK_JWT_AUDIENCE: Optional[str] = None  # e.g., "https://your-frontend-domain.com"

    # Paddle
    PADDLE_VENDOR_ID: int
    PADDLE_VENDOR_AUTH_CODE: str
    PADDLE_PUBLIC_KEY: str
    PADDLE_ENVIRONMENT: str = "sandbox"  # sandbox or production

    # OpenAI
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
