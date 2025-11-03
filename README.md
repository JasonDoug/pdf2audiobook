# PDF2AudioBook SaaS Platform

A complete SaaS platform for converting PDF documents to audiobooks using OCR and text-to-speech technology.

## Architecture

This platform follows a modern microservices architecture:

- **Frontend**: Next.js (React) with Clerk authentication
- **Backend API**: FastAPI (Python) with PostgreSQL database
- **Task Queue**: Celery with Redis for asynchronous PDF processing
- **File Storage**: AWS S3 for PDF and audio file storage
- **Payment**: Paddle for subscription and credit-based billing
- **Deployment**: Vercel (frontend) + Render/Heroku (backend)

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

## Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL
- Redis
- AWS account (for S3)
- Paddle account (for payments)
- OpenAI API key (for TTS and summarization)

### Backend Setup

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Set up database:
```bash
# Create database tables
alembic upgrade head
```

4. Start the API server:
```bash
cd backend
uvicorn main:app --reload
```

### Worker Setup

1. Start Redis server:
```bash
redis-server
```

2. Start Celery worker:
```bash
cd worker
celery -A celery_app worker --loglevel=info
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit with your Clerk and API configuration
```

3. Start development server:
```bash
npm run dev
```

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

## Deployment

### Frontend (Vercel)
1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Backend (Render/Heroku)
1. Create PostgreSQL and Redis add-ons
2. Set environment variables
3. Deploy using Docker or direct Git integration

### Worker (Render/Heroku)
1. Deploy as separate worker process
2. Configure Celery broker and result backend
3. Set up auto-scaling based on queue length

## Monitoring

- Use Celery Flower for task monitoring
- Set up logging aggregation
- Monitor AWS S3 costs
- Track Paddle payment metrics

## Security Considerations

- JWT token validation
- File upload restrictions
- Rate limiting on API endpoints
- Secure webhook signature verification
- Environment variable management

## Performance Optimization

- Implement file compression
- Use CDN for static assets
- Optimize database queries
- Implement caching strategies
- Monitor and optimize Celery queue performance

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes and add tests
4. Submit pull request

## License

MIT License - see LICENSE file for details