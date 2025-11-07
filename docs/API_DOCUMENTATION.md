# PDF2Audiobook API Documentation

## Overview

The PDF2Audiobook API provides a comprehensive REST interface for converting PDF documents to high-quality audiobooks. The API supports multiple TTS providers, real-time progress tracking, and secure file management.

**Base URL:** `https://pdf2audiobook.onrender.com` (production) or `http://localhost:8000` (development)

**Version:** v1

**Authentication:** JWT Bearer tokens via Clerk

---

## Authentication

All API requests require authentication using JWT tokens obtained from Clerk authentication.

### Getting Started with Authentication

1. **Frontend Integration**: Use Clerk's React SDK to authenticate users
2. **Token Management**: Clerk automatically manages token refresh
3. **API Requests**: Include the JWT in the Authorization header

### Authentication Flow

```javascript
// Frontend example with Clerk
import { useAuth } from '@clerk/nextjs';

function MyComponent() {
  const { getToken } = useAuth();

  const makeAuthenticatedRequest = async () => {
    const token = await getToken();
    const response = await fetch('/api/v1/jobs/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  };
}
```

### Token Verification

The API automatically verifies tokens on each request. Invalid or expired tokens return `401 Unauthorized`.

---

## Core Concepts

### Jobs
A job represents a single PDF-to-audiobook conversion request. Each job has:
- Unique ID for tracking
- Status (pending, processing, completed, failed)
- Progress percentage
- File URLs for input/output
- Processing options (voice, speed, etc.)

### Credits & Subscriptions
Users have credits for processing jobs:
- **Free Tier**: 2 conversions/month
- **Pro**: 50 conversions/month ($29.99)
- **Enterprise**: Unlimited ($99.99)
- **Credit Packs**: One-time purchases

### File Storage
- PDFs uploaded to secure AWS S3 storage
- Generated audiobooks stored with temporary URLs
- Automatic cleanup of old files

---

## API Endpoints

### Authentication

#### POST `/api/v1/auth/verify`
Verify a Clerk JWT token and sync user data.

**Request:**
```bash
curl -X POST "https://pdf2audiobook.onrender.com/api/v1/auth/verify" \
  -H "Authorization: Bearer <jwt-token>"
```

**Response (200):**
```json
{
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "credits_remaining": 45,
    "subscription_tier": "pro"
  }
}
```

#### GET `/api/v1/auth/me`
Get current user profile information.

**Response (200):**
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "credits_remaining": 45,
  "subscription_tier": "pro",
  "total_jobs": 12,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### PUT `/api/v1/auth/me`
Update user profile information.

**Request:**
```json
{
  "email": "newemail@example.com"
}
```

### Jobs

#### POST `/api/v1/jobs/`
Create a new PDF processing job.

**Request (multipart/form-data):**
```bash
curl -X POST "https://api.pdf2audiobook.com/api/v1/jobs/" \
  -H "Authorization: Bearer <jwt-token>" \
  -F "file=@document.pdf" \
  -F "voice_provider=openai" \
  -F "voice=openai_alloy" \
  -F "reading_speed=1.0" \
  -F "include_summary=true"
```

**Parameters:**
- `file` (required): PDF file (max 50MB)
- `voice_provider` (optional): "openai", "google", "aws", "azure", "elevenlabs" (default: "openai")
- `voice` (optional): Voice identifier (provider-specific)
- `reading_speed` (optional): 0.5 to 2.0 (default: 1.0)
- `include_summary` (optional): true/false (default: false)

**Response (201):**
```json
{
  "id": "job_456",
  "status": "pending",
  "progress": 0,
  "pdf_url": "https://s3.amazonaws.com/.../pdfs/user_123/document.pdf",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

**Error Responses:**
- `402 Payment Required`: Insufficient credits
- `413 Payload Too Large`: File too large
- `415 Unsupported Media Type`: Invalid file type
- `429 Too Many Requests`: Rate limit exceeded

#### GET `/api/v1/jobs/`
List user's jobs with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)
- `status` (optional): Filter by status

**Response (200):**
```json
{
  "jobs": [
    {
      "id": "job_456",
      "status": "completed",
      "progress": 100,
      "pdf_filename": "document.pdf",
      "audio_url": "https://s3.amazonaws.com/.../audio/job_456/output.mp3",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### GET `/api/v1/jobs/{job_id}`
Get detailed job information.

**Response (200):**
```json
{
  "id": "job_456",
  "status": "processing",
  "progress": 65,
  "pdf_url": "https://s3.amazonaws.com/...",
  "audio_url": null,
  "voice_provider": "openai",
  "voice": "alloy",
  "reading_speed": 1.0,
  "include_summary": true,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:32:00Z"
}
```

#### GET `/api/v1/jobs/{job_id}/status`
Get real-time job status (lightweight endpoint for polling).

**Response (200):**
```json
{
  "status": "processing",
  "progress": 65,
  "audio_url": null
}
```

### Payments

#### GET `/api/v1/payments/products`
Get available subscription plans and credit packs.

**Response (200):**
```json
{
  "products": [
    {
      "id": "prod_free",
      "name": "Free",
      "description": "2 conversions per month",
      "price": 0,
      "currency": "USD",
      "credits": 2,
      "interval": "month"
    },
    {
      "id": "prod_pro",
      "name": "Pro",
      "description": "50 conversions per month",
      "price": 29.99,
      "currency": "USD",
      "credits": 50,
      "interval": "month"
    }
  ]
}
```

#### POST `/api/v1/payments/checkout-url`
Generate a Paddle checkout URL for purchasing.

**Request:**
```json
{
  "product_id": "prod_pro",
  "success_url": "https://app.pdf2audiobook.com/success",
  "cancel_url": "https://app.pdf2audiobook.com/cancel"
}
```

**Response (200):**
```json
{
  "checkout_url": "https://checkout.paddle.com/..."
}
```

### Webhooks

#### POST `/api/v1/webhooks/paddle`
Handle Paddle payment webhooks (server-to-server only).

This endpoint is automatically called by Paddle when payments are processed. It handles:
- Subscription creation/cancellation
- Payment success/failure
- Credit allocation

**Security:** Requires valid Paddle webhook signature.

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

| Endpoint | Limit |
|----------|-------|
| POST `/api/v1/jobs/` | 10 requests/minute |
| GET `/api/v1/jobs/{id}/status` | 60 requests/minute |
| All other endpoints | 100 requests/minute |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message",
  "type": "ERROR_TYPE",
  "code": "SPECIFIC_ERROR_CODE"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INSUFFICIENT_CREDITS` | 402 | User doesn't have enough credits |
| `FILE_TOO_LARGE` | 413 | PDF file exceeds size limit |
| `INVALID_FILE_TYPE` | 415 | File is not a valid PDF |
| `JOB_NOT_FOUND` | 404 | Job ID doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_TOKEN` | 401 | Authentication token invalid |
| `SERVER_ERROR` | 500 | Internal server error |

---

## File Upload Guidelines

### Supported Formats
- PDF files only (.pdf extension)
- Maximum file size: 50MB
- Content validation: Must be valid PDF structure

### Upload Process
1. Client validates file locally (size, type)
2. API validates file on server
3. File uploaded to secure S3 storage
4. Processing job created
5. Background worker processes the file

### Security Measures
- File type validation (magic bytes)
- Virus scanning (if configured)
- Size limits enforcement
- Secure S3 bucket permissions

---

## Real-time Progress Tracking

Jobs can be tracked in real-time using polling or websockets:

### Polling Approach
```javascript
const pollJobStatus = async (jobId) => {
  const response = await fetch(`/api/v1/jobs/${jobId}/status`);
  const status = await response.json();

  if (status.status === 'completed') {
    // Download audio file
    window.location.href = status.audio_url;
  } else if (status.status === 'failed') {
    // Show error
    console.error('Job failed');
  } else {
    // Continue polling
    setTimeout(() => pollJobStatus(jobId), 2000);
  }
};
```

### Progress Stages
1. **Pending**: Job queued for processing
2. **Processing**: OCR text extraction (0-20%)
3. **Processing**: Text cleaning and chapterization (20-40%)
4. **Processing**: AI summary generation (40-60%)
5. **Processing**: Text-to-speech conversion (60-90%)
6. **Completed**: Audio file ready for download (100%)

---

## SDKs and Libraries

### JavaScript/TypeScript Client
```javascript
class PDF2AudiobookClient {
  constructor(baseUrl, getToken) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  async createJob(file, options = {}) {
    const token = await this.getToken();
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(options).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const response = await fetch(`${this.baseUrl}/api/v1/jobs/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    return response.json();
  }

  async getJobStatus(jobId) {
    const token = await this.getToken();
    const response = await fetch(`${this.baseUrl}/api/v1/jobs/${jobId}/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    return response.json();
  }
}
```

### Python Client
```python
import requests

class PDF2AudiobookAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })

    def create_job(self, pdf_file, voice_provider='openai', **options):
        files = {'file': pdf_file}
        data = {'voice_provider': voice_provider, **options}

        response = self.session.post(f'{self.base_url}/api/v1/jobs/', files=files, data=data)
        return response.json()

    def get_job_status(self, job_id):
        response = self.session.get(f'{self.base_url}/api/v1/jobs/{job_id}/status')
        return response.json()
```

---

## Integration Examples

### Complete User Flow
```javascript
// 1. User selects PDF file
const fileInput = document.getElementById('pdf-file');
const file = fileInput.files[0];

// 2. Create processing job
const job = await api.createJob(file, {
  voice_provider: 'openai',
  voice: 'alloy',
  reading_speed: 1.2,
  include_summary: true
});

// 3. Poll for completion
const pollInterval = setInterval(async () => {
  const status = await api.getJobStatus(job.id);

  updateProgress(status.progress);

  if (status.status === 'completed') {
    clearInterval(pollInterval);
    downloadAudio(status.audio_url);
  } else if (status.status === 'failed') {
    clearInterval(pollInterval);
    showError('Processing failed');
  }
}, 2000);
```

### Credit Management
```javascript
// Check credits before upload
const user = await api.getUserProfile();
if (user.credits_remaining < 1) {
  // Show payment required modal
  const products = await api.getProducts();
  showPricingModal(products);
} else {
  // Proceed with upload
  createJob(file);
}
```

---

## Best Practices

### Client Implementation
1. **Validate files client-side** before upload
2. **Show progress indicators** during upload and processing
3. **Implement exponential backoff** for polling
4. **Handle network errors gracefully**
5. **Cache user data** to reduce API calls

### Error Handling
1. **Check rate limits** before making requests
2. **Handle 402 errors** by showing payment UI
3. **Retry failed requests** with backoff
4. **Log errors** for debugging

### Performance
1. **Compress PDFs** before upload when possible
2. **Use appropriate polling intervals** (2-5 seconds)
3. **Cache product information**
4. **Lazy load job history**

---

## Support

### Getting Help
- **Documentation**: This API documentation
- **Interactive Docs**: `/docs` endpoint for testing
- **Status Page**: Check service status and incidents
- **Support**: Contact support@pdf2audiobook.com

### Common Issues
- **"Insufficient credits"**: Purchase more credits or upgrade subscription
- **"File too large"**: Compress PDF or split into smaller files
- **"Processing failed"**: Check file quality and try again
- **Rate limited**: Wait before retrying or upgrade plan

---

## Changelog

### v1.0.0 (Current)
- Initial production release
- JWT authentication with Clerk
- Multi-provider TTS support
- Real-time progress tracking
- Comprehensive error handling
- Rate limiting and security features
