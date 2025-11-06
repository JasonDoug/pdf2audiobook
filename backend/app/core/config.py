from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Core Project Settings
    PROJECT_NAME: str = "pdf2audiobook"
    PROJECT_VERSION: str = "0.1.0"

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    TESTING_MODE: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"

    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS - More restrictive defaults
    ALLOWED_HOSTS: List[str] = []

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None

    # Authentication (Clerk)
    CLERK_PEM_PUBLIC_KEY: Optional[str] = None
    CLERK_JWT_ISSUER: Optional[str] = None
    CLERK_JWT_AUDIENCE: Optional[str] = None

    # Paddle
    PADDLE_VENDOR_ID: Optional[int] = None
    PADDLE_VENDOR_AUTH_CODE: Optional[str] = None
    PADDLE_PUBLIC_KEY: Optional[str] = None
    PADDLE_ENVIRONMENT: str = "sandbox"  # sandbox or production

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # File upload limits
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf"]

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_MINUTES: int = 1

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True

        @classmethod
        def customize_sources(cls, init_settings, env_settings, file_secret_settings):
            """Customize settings sources with environment-specific priority."""
            return (
                init_settings,
                env_settings,  # Environment variables
                file_secret_settings,  # .env file
            )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    def validate_production_settings(self):
        """Validate that required production settings are configured."""
        if self.is_production:
            required_settings = [
                ("DATABASE_URL", self.DATABASE_URL),
                ("SECRET_KEY", self.SECRET_KEY),
                ("CLERK_PEM_PUBLIC_KEY", self.CLERK_PEM_PUBLIC_KEY),
                ("CLERK_JWT_ISSUER", self.CLERK_JWT_ISSUER),
                ("CLERK_JWT_AUDIENCE", self.CLERK_JWT_AUDIENCE),
            ]

            missing = [name for name, value in required_settings if not value]
            if missing:
                raise ValueError(f"Missing required production settings: {', '.join(missing)}")

            # Validate SECRET_KEY is not default
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed from default value in production")


settings = Settings()
