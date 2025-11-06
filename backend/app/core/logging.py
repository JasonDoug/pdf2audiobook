import logging
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings

class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru."""
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """Setup production-ready logging configuration."""
    # Intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL.upper())

    # Remove every other logger's handlers and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure loguru handlers based on environment
    handlers = []

    # Console handler
    if settings.LOG_FORMAT.lower() == "json":
        console_format = "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> <level>{message}</level>"
    else:
        console_format = "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> <level>{message}</level>"

    handlers.append({
        "sink": sys.stdout,
        "format": console_format,
        "level": settings.LOG_LEVEL.upper(),
        "serialize": settings.LOG_FORMAT.lower() == "json",
        "colorize": not settings.is_production,  # Disable colors in production
    })

    # File handlers for production
    if settings.is_production:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Application logs
        handlers.extend([
            {
                "sink": log_dir / "app.log",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                "level": settings.LOG_LEVEL.upper(),
                "rotation": "10 MB",
                "retention": "30 days",
                "serialize": False,
            },
            {
                "sink": log_dir / "error.log",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                "level": "ERROR",
                "rotation": "10 MB",
                "retention": "30 days",
                "serialize": False,
            },
        ])

    # Configure loguru
    logger.configure(handlers=handlers)

    # Log startup information
    logger.info(f"Logging configured for environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log format: {settings.LOG_FORMAT}")
