import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SubscriptionTier(enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VoiceProvider(enum.Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    AWS_POLLY = "aws_polly"
    AZURE = "azure"
    ELEVEN_LABS = "eleven_labs"


class ProductType(enum.Enum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"


class ConversionMode(enum.Enum):
    FULL = "full"
    SUMMARY_EXPLANATION = "summary_explanation"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    auth_provider_id = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))

    # Subscription info
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    paddle_customer_id = Column(String(255))
    one_time_credits = Column(Integer, default=0)
    monthly_credits_used = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    jobs = relationship("Job", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File info
    original_filename = Column(String(255), nullable=False)
    pdf_s3_key = Column(String(500), nullable=False)
    audio_s3_key = Column(String(500))
    pdf_s3_url = Column(String(1000))
    audio_s3_url = Column(String(1000))

    # Processing info
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text)

    # Processing options
    voice_provider = Column(Enum(VoiceProvider), default=VoiceProvider.OPENAI)
    voice_type = Column(String(50), default="default")
    reading_speed = Column(Numeric(3, 2), default=1.0)
    include_summary = Column(Boolean, default=False)
    conversion_mode = Column(Enum(ConversionMode), default=ConversionMode.FULL)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="jobs")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    paddle_product_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(ProductType), nullable=False)

    # Pricing
    price = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")

    # Credits/Tier info
    credits_included = Column(Integer)
        subscription_tier = Column(Enum(SubscriptionTier))

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="product")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Paddle info
    paddle_subscription_id = Column(String(255), unique=True)
    status = Column(String(50), default="active")

    # Billing
    next_billing_date = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    product = relationship("Product", back_populates="subscriptions")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))

    # Paddle info
    paddle_transaction_id = Column(String(255), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(50), default="completed")

    # Credits applied
    credits_added = Column(Integer)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")
    product = relationship("Product")
