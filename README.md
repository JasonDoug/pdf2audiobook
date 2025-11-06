# PDF2AudioBook SaaS Platform

A production-ready SaaS platform for converting PDF documents to high-quality audiobooks using advanced OCR and text-to-speech technology.

## 🚀 Features

### Core Functionality
- **PDF Processing**: Extract text from PDFs using OCR technology
- **Multiple TTS Providers**: Support for OpenAI, Google Cloud, AWS Polly, Azure, and ElevenLabs
- **Voice Customization**: Choose from various voices and adjust reading speeds (0.5x to 2.0x)
- **AI-Powered Summaries**: Generate intelligent summaries for complex documents
- **Progress Tracking**: Real-time processing status updates
- **File Management**: Secure upload/download with AWS S3 integration

### User Management
- **Authentication**: Secure JWT-based authentication with Clerk integration
- **Subscription Tiers**: Free, Pro, and Enterprise plans
- **Credit System**: Flexible one-time credit purchases
- **Usage Tracking**: Monitor credits and subscription usage

### Business Model
- **Free Tier**: 2 PDF conversions per month
- **Pro Subscription**: 50 conversions per month ($29.99/month)
- **Enterprise**: Unlimited conversions ($99.99/month)
- **Credit Packs**: One-time purchases for occasional users

## 🏗️ Architecture

This platform follows a modern microservices architecture with production-grade security and monitoring:

- **Frontend**: Next.js (React) with Clerk authentication and Tailwind CSS
- **Backend API**: FastAPI (Python) with comprehensive security middleware
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Task Queue**: Celery with Redis for asynchronous PDF processing
- **File Storage**: AWS S3 with secure upload/download
- **Payment Processing**: Paddle integration for subscriptions and credits
- **Deployment**: Docker containerization with production-ready configurations

## Features

### User Management
- User registration/login via Clerk
- Subscription tiers (Free, Pro, Enterprise)
- Credit-based system for one-time purchases

### PDF Processing
- OCR text extraction from PDFs
- Multiple voice options and reading speeds
- Optional AI-powered summaries
- Progress tracking during processing

### Business Model
- **Free Tier**: 2 PDF conversions per month
- **Pro Subscription**: 50 conversions per month ($29.99/month)
- **Enterprise**: Unlimited conversions ($99.99/month)
- **Credit Packs**: One-time purchases for occasional users

## Project Structure

```
pdf2audiobook/
├── backend/                 # FastAPI backend
│   └── app/
│       ├── api/v1/         # API endpoints
│       ├── core/           # Configuration and database
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas
│       └── services/       # Business logic
├── frontend/               # Next.js frontend
├── worker/                 # Celery worker
│   ├── celery_app.py      # Celery configuration
│   ├── tasks.py           # Background tasks
│   └── pdf_pipeline.py    # PDF processing logic
└── pyproject.toml         # Project dependencies
```

## Docker Setup

1.  **Build and run the containers**:

    ```bash
    docker-compose up --build
    ```

2.  **Access the application**:

    -   Frontend: [http://localhost:3000](http://localhost:3000)
    -   Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)


## API Endpoints

### Authentication
- `POST /api/v1/auth/verify` - Verify JWT token
- `GET /api/v1/auth/me` - Get current user info
- `PUT /api/v1/auth/me` - Update user profile

### Jobs
- `POST /api/v1/jobs/` - Create new PDF processing job
- `GET /api/v1/jobs/` - List user's jobs
- `GET /api/v1/jobs/{job_id}` - Get job details
- `GET /api/v1/jobs/{job_id}/status` - Get job status

### Payments
- `GET /api/v1/payments/products` - List available products
- `POST /api/v1/payments/checkout-url` - Generate checkout URL

### Webhooks
- `POST /api/v1/webhooks/paddle` - Handle Paddle webhooks

## Database Schema

### Users Table
- Authentication and profile information
- Subscription tier and credits
- Paddle customer ID

### Jobs Table
- PDF processing jobs
- File locations and status
- Processing options

### Products Table
- Subscription plans and credit packs
- Pricing and features

### Subscriptions Table
- User subscription records
- Billing information

### Transactions Table
- Payment history
- Credit allocations

## Production Deployment

### Environment Configuration
The application uses environment-aware configuration with validation:

```bash
# Required Environment Variables
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0
SECRET_KEY=your-256-bit-secret-key
CLERK_PEM_PUBLIC_KEY=your-clerk-public-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET_NAME=your-bucket-name
PADDLE_VENDOR_ID=your-vendor-id
PADDLE_VENDOR_AUTH_CODE=your-auth-code
OPENAI_API_KEY=your-openai-key

# Production Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_HOSTS=https://yourdomain.com,https://api.yourdomain.com
```

### Docker Deployment

#### Backend API
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Worker Service
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["celery", "worker", "-A", "worker.celery_app", "--loglevel=info"]
```

### Cloud Deployment Options

#### Backend & Worker (Railway/Render)
1. Connect GitHub repository
2. Configure PostgreSQL and Redis services
3. Set production environment variables
4. Enable health checks and monitoring
5. Configure auto-scaling for workers

#### Frontend (Vercel/Netlify)
1. Connect GitHub repository
2. Configure build settings for Next.js
3. Set API endpoint environment variables
4. Enable preview deployments for staging

### Production Checklist
- [ ] Environment variables configured and validated
- [ ] Database migrations applied
- [ ] SSL/TLS certificates configured
- [ ] Domain DNS configured
- [ ] Monitoring and alerting set up
- [ ] Backup procedures established
- [ ] Security headers verified
- [ ] Rate limiting configured
- [ ] Health checks passing

## Monitoring & Observability

### Application Monitoring
- Health check endpoints (`/health`) for service availability
- Structured JSON logging with environment-specific handlers
- Request/response logging middleware
- Performance metrics collection (response times, error rates)

### Background Processing
- Celery Flower dashboard for task queue monitoring
- Real-time worker status and queue lengths
- Task retry mechanisms with exponential backoff
- Progress tracking for long-running PDF processing jobs

### Infrastructure Monitoring
- Database connection pool monitoring
- Redis/Celery broker health checks
- AWS S3 storage usage and cost tracking
- Paddle payment webhook monitoring

### Logging & Alerting
- Environment-specific log levels (DEBUG/INFO in dev, WARN/ERROR in prod)
- Log rotation and retention policies
- Error aggregation and alerting
- Audit trails for security events

## Security Considerations

### Authentication & Authorization
- JWT token validation with Clerk integration
- Role-based access control for user operations
- Secure token refresh mechanisms
- Comprehensive input validation and sanitization

### API Security
- Rate limiting on all endpoints (configurable limits)
- CORS configuration with strict origin control
- Request/response compression for performance
- Security headers middleware (HSTS, CSP, X-Frame-Options)
- File upload restrictions with type and size validation

### Data Protection
- Secure webhook signature verification for Paddle payments
- Environment variable management with validation
- Database connection pooling and prepared statements
- Encrypted file storage with AWS S3

### Production Security Features
- Structured logging with sensitive data filtering
- Comprehensive error handling without information leakage
- Health check endpoints for monitoring
- Audit logging for critical operations

## Performance Optimization

- Implement file compression
- Use CDN for static assets
- Optimize database queries
- Implement caching strategies
- Monitor and optimize Celery queue performance

## API Documentation

### Interactive API Docs
Access the interactive API documentation at `http://localhost:8000/docs` when running locally, or `/docs` in production.

### Authentication
All API endpoints require authentication via JWT tokens obtained from Clerk. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Rate Limiting
- Job creation: 10 requests per minute per user
- General endpoints: 100 requests per minute per user
- File uploads: 50MB per file, 5 files per minute

### Error Handling
The API returns structured error responses:
```json
{
  "detail": "Error message",
  "type": "error_type",
  "code": "ERROR_CODE"
}
```

## Development

### Local Setup
1. Clone the repository
2. Install dependencies: `uv sync`
3. Set up environment variables (copy `.env.example`)
4. Run database migrations: `alembic upgrade head`
5. Start services: `docker-compose up`

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest backend/tests/api/v1/test_jobs.py
```

### Code Quality
```bash
# Lint code
ruff check .

# Format code
ruff format .

# Type checking
mypy backend/
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run tests and linting: `make test && make lint`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Submit pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints for all functions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages

## License

MIT License - see LICENSE file for details