from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    """Enumeration for user subscription tiers."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class JobStatus(str, Enum):
    """Enumeration for the status of a PDF processing job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductType(str, Enum):
    """Enumeration for product types (subscription or one-time purchase)."""

    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"


class VoiceProvider(str, Enum):
    """Enumeration for supported Text-to-Speech (TTS) providers."""

    OPENAI = "openai"
    GOOGLE = "google"
    AWS_POLLY = "aws_polly"
    AZURE = "azure"
    ELEVEN_LABS = "eleven_labs"


# --- User Schemas ---


class UserBase(BaseModel):
    """Base schema for user properties."""

    email: EmailStr = Field(
        ..., example="user@example.com", description="User's unique email address."
    )
    first_name: Optional[str] = Field(
        None, example="John", description="User's first name."
    )
    last_name: Optional[str] = Field(
        None, example="Doe", description="User's last name."
    )


class UserCreate(UserBase):
    """Schema for creating a new user, including their third-party auth ID."""

    auth_provider_id: str = Field(
        ...,
        example="clerk_123xyz",
        description="Unique identifier from the authentication provider (e.g., Clerk).",
    )


class UserUpdate(BaseModel):
    """Schema for updating a user's profile information."""

    first_name: Optional[str] = Field(
        None, example="John", description="User's updated first name."
    )
    last_name: Optional[str] = Field(
        None, example="Doe", description="User's updated last name."
    )


class User(UserBase):
    """Schema for representing a user, returned from the API."""

    id: int = Field(
        ..., example=1, description="Internal unique identifier for the user."
    )
    auth_provider_id: str = Field(
        ...,
        example="clerk_123xyz",
        description="Unique identifier from the authentication provider.",
    )
    subscription_tier: SubscriptionTier = Field(
        ...,
        example=SubscriptionTier.PRO,
        description="User's current subscription tier.",
    )
    paddle_customer_id: Optional[str] = Field(
        None, example="ctm_123abc", description="User's customer ID from Paddle."
    )
    one_time_credits: int = Field(
        ..., example=10, description="Number of one-time credits the user has."
    )
    monthly_credits_used: int = Field(
        ...,
        example=5,
        description="Number of monthly subscription credits used in the current billing cycle.",
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the user was created."
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the user was last updated."
    )

    class Config:
        from_attributes = True


# --- Job Schemas ---


class JobBase(BaseModel):
    """Base schema for job properties, used for creation."""

    original_filename: str = Field(
        ...,
        example="my_document.pdf",
        description="The original filename of the uploaded PDF.",
    )
    voice_provider: VoiceProvider = Field(
        VoiceProvider.OPENAI,
        description="The TTS provider to use for audio generation.",
    )
    voice_type: str = Field(
        "default",
        example="alloy",
        description="The specific voice to use from the selected provider.",
    )
    reading_speed: float = Field(
        1.0,
        ge=0.5,
        le=2.0,
        description="The reading speed for the audiobook (0.5x to 2.0x).",
    )
    include_summary: bool = Field(
        False,
        description="Whether to generate and include an AI summary at the beginning of the audiobook.",
    )


class JobCreate(JobBase):
    """Schema used for creating a new job. Inherits all fields from JobBase."""

    pass


class JobUpdate(BaseModel):
    """Schema for updating a job's status or progress."""

    status: Optional[JobStatus] = Field(None, description="The new status of the job.")

    progress_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="The current processing progress (0-100)."
    )

    error_message: Optional[str] = Field(
        None, description="An error message if the job failed."
    )

    audio_s3_url: Optional[str] = Field(
        None, description="The public URL for the generated audio file."
    )


class Job(JobBase):
    """Schema for representing a job, returned from the API."""

    id: int = Field(
        ..., example=42, description="Internal unique identifier for the job."
    )
    user_id: int = Field(
        ..., example=1, description="The ID of the user who created the job."
    )
    pdf_s3_key: str = Field(
        ...,
        example="pdfs/1/my_document.pdf",
        description="The S3 key for the stored PDF file.",
    )
    audio_s3_key: Optional[str] = Field(
        None,
        example="audio/1/42.mp3",
        description="The S3 key for the generated audio file.",
    )
    pdf_s3_url: Optional[str] = Field(
        None,
        example="https://bucket.s3.amazonaws.com/pdfs/1/my_document.pdf",
        description="The public URL for the PDF file.",
    )
    audio_s3_url: Optional[str] = Field(
        None,
        example="https://bucket.s3.amazonaws.com/audio/1/42.mp3",
        description="The public URL for the generated audio file.",
    )
    status: JobStatus = Field(
        ..., example=JobStatus.COMPLETED, description="The current status of the job."
    )
    progress_percentage: int = Field(
        ..., example=100, ge=0, le=100, description="The processing progress (0-100)."
    )
    error_message: Optional[str] = Field(
        None, description="An error message if the job failed."
    )
    created_at: datetime = Field(..., description="Timestamp when the job was created.")
    started_at: Optional[datetime] = Field(
        None, description="Timestamp when processing started."
    )
    completed_at: Optional[datetime] = Field(
        None, description="Timestamp when processing was completed."
    )

    class Config:
        from_attributes = True


# --- Auth Schemas ---


class Token(BaseModel):
    """Schema for the access token returned upon successful authentication."""

    access_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="A JWT access token.",
    )
    token_type: str = Field("bearer", description="The type of the token.")


class TokenData(BaseModel):
    """Schema for the data encoded within the JWT access token."""

    user_id: Optional[int] = Field(
        None, description="The user ID associated with the token."
    )
