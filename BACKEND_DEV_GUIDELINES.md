# PDF2AudioBook Backend Development Guidelines

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Code Organization](#code-organization)
4. [API Development Standards](#api-development-standards)
5. [Database Guidelines](#database-guidelines)
6. [Task Queue & Worker Guidelines](#task-queue--worker-guidelines)
7. [PDF Pipeline Integration](#pdf-pipeline-integration)
8. [Error Handling & Logging](#error-handling--logging)
9. [Security Guidelines](#security-guidelines)
10. [Testing Guidelines](#testing-guidelines)
11. [Performance Considerations](#performance-considerations)
12. [Deployment Guidelines](#deployment-guidelines)

## 🏗️ Architecture Overview

### System Components
```
Frontend (Next.js) 
    ↓ HTTP Requests (REST API)
FastAPI Backend
    ↓ Queue Tasks
Celery Workers + Redis
    ↓ Direct Calls
PDF Processing Pipeline
    ↓ Multi-Provider TTS
├── OpenAI TTS
├── Google Cloud TTS  
├── AWS Polly
├── Azure Speech
└── ElevenLabs
    ↓ External Services
├── AWS S3 (Storage)
├── OpenAI API (Summary)
└── Tesseract OCR (Fallback)
```

### Key Interfaces
- **API Layer**: HTTP endpoints, authentication, validation
- **Service Layer**: Business logic, database operations
- **Task Queue**: Asynchronous job processing
- **Pipeline Layer**: Pure PDF-to-audio conversion logic

## 🛠️ Development Setup

### Prerequisites
```bash
# Required software
Python 3.12+
PostgreSQL 14+
Redis 6+
Node.js 18+ (for frontend development)
```

### Environment Setup
```bash
# Clone and setup
git clone <repository>
cd pdf2audiobook

# Install Python dependencies
uv sync

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Setup database
createdb pdf2audiobook
alembic upgrade head

# Start Redis
redis-server

# Start backend (terminal 1)
cd backend
uvicorn main:app --reload

# Start worker (terminal 2)
cd worker
celery -A celery_app worker --loglevel=info
```

### Environment Variables
```bash
# Core settings
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/pdf2audiobook

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=pdf2audiobook-uploads

# Authentication
CLERK_PEM_PUBLIC_KEY=your-clerk-public-key

# Payments
PADDLE_VENDOR_ID=your-vendor-id
PADDLE_VENDOR_AUTH_CODE=your-vendor-auth-code
PADDLE_PUBLIC_KEY=your-paddle-public-key

# OpenAI (TTS + Summary)
OPENAI_API_KEY=your-openai-api-key

# Google Cloud Text-to-Speech
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# AWS Polly
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Azure Cognitive Services Speech
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=your-azure-region

# ElevenLabs
ELEVENLABS_API_KEY=your-elevenlabs-api-key
```

## 📁 Code Organization

### Directory Structure
```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── jobs.py       # Job management endpoints
│   │   ├── payments.py   # Payment endpoints
│   │   └── webhooks.py   # Webhook handlers
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings and environment
│   │   └── database.py   # Database connection
│   ├── models/           # SQLAlchemy models
│   │   └── __init__.py   # All database models
│   ├── schemas/          # Pydantic schemas
│   │   └── __init__.py   # Request/response models
│   └── services/         # Business logic
│       ├── auth.py       # Authentication service
│       ├── job.py        # Job management service
│       ├── payment.py    # Payment processing
│       ├── storage.py    # S3 file operations
│       └── user.py       # User management
├── main.py              # FastAPI application entry
└── tests/               # Test files
```

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Endpoints**: `/api/v1/resource_name`

## 🚀 API Development Standards

### Endpoint Structure
```python
# Standard endpoint pattern
@router.post("/", response_model=ResponseSchema)
async def create_resource(
    resource_data: RequestSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Validate business logic
    # 2. Process request
    # 3. Return response
    pass
```

### Request/Response Patterns
```python
# Always use Pydantic schemas
class JobCreate(BaseModel):
    original_filename: str
    voice_type: str = "default"
    reading_speed: float = 1.0

class JobResponse(BaseModel):
    id: int
    status: JobStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Error Handling
```python
# Standardized error responses
@router.get("/{job_id}")
async def get_job(job_id: int):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job
```

### Authentication
```python
# All protected endpoints require authentication
@router.post("/protected-endpoint")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    # current_user is guaranteed to be authenticated
    pass
```

## 🗄️ Database Guidelines

### Model Definition
```python
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="jobs")
```

### Service Layer Pattern
```python
class JobService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_job(self, user_id: int, job_data: JobCreate) -> Job:
        job = Job(user_id=user_id, **job_data.dict())
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def get_user_jobs(self, user_id: int, skip: int = 0, limit: int = 50):
        return self.db.query(Job).filter(
            Job.user_id == user_id
        ).offset(skip).limit(limit).all()
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## ⚙️ Task Queue & Worker Guidelines

### Task Definition
```python
@celery_app.task(bind=True)
def process_pdf_task(self, job_id: int):
    """
    Process a PDF file and convert it to audio
    """
    db = SessionLocal()
    
    try:
        # 1. Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # 2. Update status to processing
        job_service.update_job_status(job_id, JobStatus.PROCESSING, 0)
        
        # 3. Process file
        result = process_file(job)
        
        # 4. Update final status
        job_service.update_job_status(job_id, JobStatus.COMPLETED, 100)
        
        return result
        
    except Exception as e:
        # Update job with error
        job_service.update_job_status(job_id, JobStatus.FAILED, str(e))
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()
```

### Progress Tracking
```python
# Update progress at key milestones
self.update_state(state='PROGRESS', meta={'progress': 25})
job_service.update_job_status(job_id, JobStatus.PROCESSING, 25)
```

### Task Configuration
```python
# celery_app.py
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
```

## 📄 PDF Pipeline Integration

### Multi-Provider TTS Architecture
The pipeline supports 5 TTS providers with a unified interface:

```python
# TTS Provider Interface
class TTSProvider(ABC):
    @abstractmethod
    def text_to_audio(self, text: str, voice_id: str, speed: float) -> bytes:
        pass

# Supported Providers
TTS_PROVIDERS = {
    "openai": OpenAITTS,           # OpenAI TTS-1
    "google": GoogleTTS,           # Google Cloud Text-to-Speech
    "aws_polly": AWSPollyTTS,      # AWS Polly
    "azure": AzureTTS,             # Azure Cognitive Services
    "eleven_labs": ElevenLabsTTS   # ElevenLabs
}
```

### Pipeline Interface
```python
class PDFToAudioPipeline:
    def process_pdf(
        self, 
        pdf_path: str,
        voice_provider: str = "openai",
        voice_type: str = "default",
        reading_speed: float = 1.0,
        include_summary: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> bytes:
        """
        Convert PDF to audio using intelligent text extraction and multi-provider TTS
        Returns: Audio data as bytes (MP3 format)
        """
```

### Worker Integration
```python
# Worker calls pipeline with voice provider from job model
pipeline = PDFToAudioPipeline()
audio_data = pipeline.process_pdf(
    pdf_path=pdf_path,
    voice_provider=job.voice_provider.value,  # Uses VoiceProvider enum
    voice_type=job.voice_type,
    reading_speed=float(job.reading_speed),
    include_summary=job.include_summary,
    progress_callback=lambda progress: job_service.update_job_status(
        job_id, JobStatus.PROCESSING, progress
    )
)
```

### Intelligent Text Extraction
```python
def _extract_text(self, pdf_path: str) -> str:
    """
    Smart text extraction with OCR fallback:
    1. Try PyMuPDF text extraction first (fast, accurate for text PDFs)
    2. If extracted text < 100 chars, fall back to OCR
    3. OCR uses pdf2image + pytesseract at 300 DPI
    """
    with fitz.open(pdf_path) as doc:
        text = "".join(page.get_text() for page in doc)
    
    # Use OCR only if text extraction fails
    if len(text.strip()) < 100:
        return self._ocr_pdf(pdf_path)
    return text
```

### Progress Tracking
```python
# Detailed progress milestones
def process_pdf(self, pdf_path: str, progress_callback=None):
    # 5% - Start processing
    progress_callback(5)
    
    # 15% - Text extraction complete
    raw_text = self._extract_text(pdf_path)
    progress_callback(15)
    
    # 35% - Text cleanup and optional summary complete
    cleaned_text = self._advanced_text_cleanup(raw_text)
    final_text = self._get_final_text(cleaned_text, include_summary)
    progress_callback(35)
    
    # 40-95% - Chapter-by-chapter TTS processing
    chapters = self._chapterize_text(final_text)
    for i, chapter_text in enumerate(chapters):
        progress = 40 + int((i / len(chapters)) * 55)
        progress_callback(progress)
        # Process chapter with selected TTS provider
    
    # 100% - Audio assembly complete
    progress_callback(100)
```

### Advanced Text Processing
```python
def _advanced_text_cleanup(self, text: str) -> str:
    """
    Comprehensive text cleanup:
    - Normalize whitespace and line breaks
    - Fix common encoding issues (â, â, â, etc.)
    - Replace ligatures (ﬁ → fi, ﬂ → fl)
    - Remove excessive spacing
    """

def _chapterize_text(self, text: str) -> List[str]:
    """
    Intelligent chapterization:
    - Detect headings (CHAPTER, SECTION, or ALL CAPS)
    - Group sentences into logical chapters
    - Minimum 20 sentences per chapter
    - Fallback to single chapter if no headings found
    """

def _generate_summary(self, text: str) -> str:
    """
    AI-powered summary generation:
    - Uses OpenAI GPT-3.5-turbo for summarization
    - Truncates to 12,000 characters for API limits
    - 150-word target summary
    - Fallback to text truncation if API fails
    """
```

## 🎤 TTS Provider Configuration

### Provider Selection Strategy
```python
# VoiceProvider enum in models
class VoiceProvider(enum.Enum):
    OPENAI = "openai"           # Fast, cost-effective, good quality
    GOOGLE = "google"           # High quality, more voices
    AWS_POLLY = "aws_polly"      # Reliable, SSML support
    AZURE = "azure"             # Neural voices, enterprise
    ELEVEN_LABS = "eleven_labs" # Premium quality, higher cost
```

### Voice Mapping by Provider
```python
# OpenAI Voice Mapping
OPENAI_VOICES = {
    "default": "alloy",
    "female": "nova", 
    "male": "onyx"
}

# Google Voice Mapping  
GOOGLE_VOICES = {
    "default": "en-US-Neural2-D",
    "female": "en-US-Neural2-F",
    "male": "en-US-Neural2-D"
}

# AWS Polly Voice Mapping
POLLY_VOICES = {
    "default": "Joanna",
    "female": "Joanna",
    "male": "Matthew"
}

# Azure Voice Mapping
AZURE_VOICES = {
    "default": "en-US-JennyNeural",
    "female": "en-US-JennyNeural", 
    "male": "en-US-GuyNeural"
}

# ElevenLabs Voice Mapping
ELEVENLABS_VOICES = {
    "default": "Rachel",
    "female": "Rachel",
    "male": "Adam"
}
```

### Speed Control Implementation
```python
# Different providers handle speed differently:

# OpenAI: Direct speed parameter
response = client.audio.speech.create(
    model="tts-1", voice=voice, input=text, speed=speed
)

# AWS Polly: SSML prosody rate
rate = f"{int(speed * 100)}%"
ssml = f'<speak><prosody rate="{rate}">{text}</prosody></speak>'

# Azure: SSML prosody rate  
rate = f"{speed:.2f}"
ssml = f'<speak><voice name="{voice}"><prosody rate="{rate}">{text}</prosody></voice></speak>'

# Google: Speaking rate in config
audio_config = texttospeech.AudioConfig(
    speaking_rate=speed
)

# ElevenLabs: Speed controlled in voice studio settings
# No direct speed parameter in API
```

### Provider-Specific Error Handling
```python
class TTSManager:
    def get_provider(self, provider_name: str) -> TTSProvider:
        try:
            if provider_name in self._instances:
                return self._instances[provider_name]
            
            provider_class = self._provider_map.get(provider_name)
            if not provider_class:
                raise ValueError(f"Unsupported TTS provider: {provider_name}")
            
            # Instantiate provider - credential errors surface here
            instance = provider_class()
            self._instances[provider_name] = instance
            return instance
            
        except Exception as e:
            # Log provider-specific initialization errors
            logger.error(f"Failed to initialize {provider_name} TTS: {e}")
            raise
```

### Cost and Quality Considerations
- **OpenAI**: Fastest processing, lowest cost, good quality
- **Google**: Higher quality, more voice options, moderate cost  
- **AWS Polly**: Reliable, SSML support, enterprise features
- **Azure**: Neural voices, good for enterprise, moderate cost
- **ElevenLabs**: Premium quality, highest cost, best for narration

### Provider Fallback Strategy
```python
# Future enhancement: automatic fallback
def get_audio_with_fallback(
    text: str, 
    primary_provider: str,
    fallback_providers: List[str] = ["openai", "google"]
):
    for provider_name in [primary_provider] + fallback_providers:
        try:
            provider = tts_manager.get_provider(provider_name)
            return provider.text_to_audio(text, voice, speed)
        except Exception as e:
            logger.warning(f"Provider {provider_name} failed: {e}")
            continue
    
    raise Exception("All TTS providers failed")
```

## 🚨 Error Handling & Logging

### Structured Logging
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/jobs")
async def create_job(job_data: JobCreate):
    logger.info(f"Creating job for user {current_user.id}")
    
    try:
        job = job_service.create_job(current_user.id, job_data)
        logger.info(f"Job {job.id} created successfully")
        return job
        
    except ValueError as e:
        logger.warning(f"Invalid job data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Error Categories
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing/invalid authentication
- **402 Payment Required**: Insufficient credits
- **404 Not Found**: Resource doesn't exist
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected errors

### Task Error Handling
```python
@celery_app.task(bind=True)
def process_pdf_task(self, job_id: int):
    try:
        # Process job
        return result
        
    except ValueError as e:
        # User error - don't retry
        logger.error(f"Invalid job {job_id}: {e}")
        job_service.update_job_status(job_id, JobStatus.FAILED, str(e))
        
    except Exception as e:
        # System error - retry
        logger.error(f"Processing failed for job {job_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

## 🔒 Security Guidelines

### Authentication
```python
# Always validate JWT tokens
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        user_data = verify_clerk_token(credentials.credentials)
        user = user_service.get_user_by_auth_id(user_data["auth_provider_id"])
        if not user:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
```

### Input Validation
```python
# Use Pydantic for all input validation
class JobCreate(BaseModel):
    voice_type: str = Field(default="default", regex="^(default|female|male|child)$")
    reading_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    include_summary: bool = False
```

### File Upload Security
```python
# Validate file uploads
async def create_job(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Check file type
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Check file size (10MB limit)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
```

### Rate Limiting
```python
# Implement rate limiting for expensive operations
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/jobs")
@limiter.limit("5/minute")
async def create_job(request: Request, ...):
    # Implementation
```

## 🧪 Testing Guidelines

### Test Structure
```python
# tests/test_jobs.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestJobs:
    def test_create_job_success(self, mock_user, mock_storage):
        """Test successful job creation"""
        response = client.post(
            "/api/v1/jobs/",
            files={"file": ("test.pdf", b"pdf content", "application/pdf")},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"
    
    def test_create_job_unauthorized(self):
        """Test job creation without authentication"""
        response = client.post("/api/v1/jobs/")
        assert response.status_code == 401
    
    def test_create_job_invalid_file(self):
        """Test job creation with invalid file"""
        response = client.post(
            "/api/v1/jobs/",
            files={"file": ("test.txt", b"text content", "text/plain")},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 400
```

### Test Database
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Task Testing
```python
# tests/test_tasks.py
import pytest
from worker.tasks import process_pdf_task
from unittest.mock import Mock, patch

class TestTasks:
    @patch('worker.tasks.PDFToAudioPipeline')
    @patch('worker.tasks.StorageService')
    def test_process_pdf_success(self, mock_storage, mock_pipeline):
        """Test successful PDF processing"""
        # Setup mocks
        mock_pipeline.return_value.process_pdf.return_value = b"audio data"
        
        # Execute task
        result = process_pdf_task(1)
        
        # Assertions
        assert result["status"] == "completed"
        mock_pipeline.return_value.process_pdf.assert_called_once()
```

## ⚡ Performance Considerations

### Database Optimization
```python
# Use indexes for frequently queried fields
class Job(Base):
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(Enum(JobStatus), index=True)
    created_at = Column(DateTime(timezone=True), index=True)

# Use pagination for large result sets
def get_user_jobs(self, user_id: int, skip: int = 0, limit: int = 50):
    return self.db.query(Job).filter(
        Job.user_id == user_id
    ).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
```

### Caching Strategy
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Cache expensive operations
@router.get("/products")
@cache(expire=300)  # 5 minutes
async def get_products():
    return payment_service.get_active_products()
```

### Async File Operations
```python
# Use async for file uploads
async def upload_file(self, file: UploadFile, key: str) -> str:
    file_content = await file.read()
    
    # Upload to S3 asynchronously
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, 
        lambda: self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_content
        )
    )
```

## 🚀 Deployment Guidelines

### Production Configuration
```python
# app/core/config.py
class Settings(BaseSettings):
    DEBUG: bool = False
    DATABASE_URL: str  # Use production database
    REDIS_URL: str     # Use production Redis
    
    class Config:
        env_file = ".env.production"
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment-Specific Settings
```bash
# .env.production
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-host:5432/pdf2audiobook
REDIS_URL=redis://prod-host:6379/0
AWS_ACCESS_KEY_ID=prod-access-key
AWS_SECRET_ACCESS_KEY=prod-secret-key
```

### Monitoring
```python
# Add health checks
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "s3": check_s3_connection()
    }
```

## 📝 Additional Backend API Requirements

### Missing Components to Implement

1. **Rate Limiting Middleware**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   ```

2. **Request Logging Middleware**
   ```python
   import time
   import logging
   
   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       start_time = time.time()
       response = await call_next(request)
       process_time = time.time() - start_time
       
       logging.info(
           f"{request.method} {request.url.path} - "
           f"Status: {response.status_code} - "
           f"Time: {process_time:.4f}s"
       )
       return response
   ```

3. **API Versioning Strategy**
   ```python
   # Use path-based versioning
   @app.get("/api/v1/jobs/")
   # Future: @app.get("/api/v2/jobs/")
   ```

4. **Response Compression**
   ```python
   from fastapi.middleware.gzip import GZipMiddleware
   
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

5. **CORS Configuration**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=settings.ALLOWED_HOSTS,
       allow_credentials=True,
       allow_methods=["GET", "POST", "PUT", "DELETE"],
       allow_headers=["*"],
   )
   ```

6. **Database Connection Pooling**
   ```python
   # app/core/database.py
   engine = create_engine(
       settings.DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True,
       pool_recycle=3600
   )
   ```

7. **Background Task Scheduler**
   ```python
   # For periodic cleanup tasks
   from celery.schedules import crontab
   
   celery_app.conf.beat_schedule = {
       'cleanup-old-files': {
           'task': 'worker.tasks.cleanup_old_files',
           'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
       },
   }
   ```

This comprehensive guide covers all aspects of backend development for the PDF2AudioBook SaaS platform. Follow these guidelines to maintain code quality, security, and performance standards.