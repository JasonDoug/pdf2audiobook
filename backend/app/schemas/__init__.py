from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProductType(str, Enum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    auth_provider_id: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class User(UserBase):
    id: int
    auth_provider_id: str
    subscription_tier: SubscriptionTier
    paddle_customer_id: Optional[str] = None
    one_time_credits: int
    monthly_credits_used: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Job schemas
class JobBase(BaseModel):
    original_filename: str
    voice_type: str = "default"
    reading_speed: float = 1.0
    include_summary: bool = False

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress_percentage: Optional[int] = None
    error_message: Optional[str] = None

class Job(JobBase):
    id: int
    user_id: int
    pdf_s3_key: str
    audio_s3_key: Optional[str] = None
    pdf_s3_url: Optional[str] = None
    audio_s3_url: Optional[str] = None
    status: JobStatus
    progress_percentage: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: ProductType
    price: Optional[float] = None
    currency: str = "USD"
    credits_included: Optional[int] = None
    subscription_tier: Optional[SubscriptionTier] = None

class ProductCreate(ProductBase):
    paddle_product_id: str

class Product(ProductBase):
    id: int
    paddle_product_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Subscription schemas
class SubscriptionBase(BaseModel):
    status: str = "active"

class SubscriptionCreate(SubscriptionBase):
    user_id: int
    product_id: int
    paddle_subscription_id: Optional[str] = None

class Subscription(SubscriptionBase):
    id: int
    user_id: int
    product_id: int
    paddle_subscription_id: Optional[str] = None
    next_billing_date: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    currency: str = "USD"
    status: str = "completed"
    credits_added: Optional[int] = None

class TransactionCreate(TransactionBase):
    user_id: int
    product_id: Optional[int] = None
    paddle_transaction_id: str

class Transaction(TransactionBase):
    id: int
    user_id: int
    product_id: Optional[int] = None
    paddle_transaction_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None