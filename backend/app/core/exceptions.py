"""
Custom exception classes for the application.

These exceptions allow for more specific error handling and clearer,
more informative logging and API error responses.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Union

class AppException(Exception):
    """Base class for all application-specific exceptions."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# --- Pipeline-related Exceptions ---

class PDFProcessingError(AppException):
    """Raised for general errors during the PDF processing pipeline."""
    def __init__(self, message: str = "An error occurred during PDF processing."):
        super().__init__(message, status_code=500)

class TextExtractionError(PDFProcessingError):
    """Raised when text cannot be extracted from a PDF, possibly due to corruption or being image-only without successful OCR."""
    def __init__(self, message: str = "Failed to extract any text from the provided PDF."):
        super().__init__(message, status_code=400)  # Bad Request, as it's likely a user file issue

class TTSServiceError(PDFProcessingError):
    """Raised when a text-to-speech service fails."""
    def __init__(self, provider: str, original_error: str):
        message = f"The '{provider}' text-to-speech service failed. Details: {original_error}"
        super().__init__(message, status_code=502)  # Bad Gateway, as it's an upstream service error

class SummaryGenerationError(PDFProcessingError):
    """Raised when the summary generation (e.g., OpenAI API) fails."""
    def __init__(self, original_error: str):
        message = f"Failed to generate summary. Details: {original_error}"
        super().__init__(message, status_code=502) # Bad Gateway

class StorageError(AppException):
    """Raised for errors related to file storage operations (e.g., S3)."""
    def __init__(self, message: str = "A storage service error occurred."):
        super().__init__(message, status_code=500)


# --- Exception Handlers ---

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with proper logging and response formatting."""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} - Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with proper logging and generic error response."""
    logger.error(
        f"Unexpected error: {str(exc)} - Path: {request.url.path} - Headers: {dict(request.headers)}"
    )

    # Don't expose internal error details in production
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "An unexpected error occurred. Please try again later.",
                "status_code": 500
            }
        }
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(
        f"Application Exception: {exc.status_code} - {exc.message} - Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "application_error",
                "message": exc.message,
                "status_code": exc.status_code
            }
        }
    )