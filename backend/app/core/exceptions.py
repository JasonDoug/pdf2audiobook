"""
Custom exception classes for the application.

These exceptions allow for more specific error handling and clearer,
more informative logging and API error responses.
"""

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