# PDF2Audiobook API Testing Guide

## Base URL
```
https://pdf2audiobook.onrender.com
```

## Authentication
All endpoints except health checks require a JWT token from Clerk. Replace `<jwt-token>` with your actual token.

---

## Health Check
```bash
# Check API health
curl -X GET "https://pdf2audiobook.onrender.com/health"
```

---

## Authentication Endpoints

### Verify Token
```bash
curl -X POST "https://pdf2audiobook.onrender.com/api/v1/auth/verify" \
  -H "Authorization: Bearer <jwt-token>"
```

### Get User Profile
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/auth/me" \
  -H "Authorization: Bearer <jwt-token>"
```

### Update User Profile
```bash
curl -X PUT "https://pdf2audiobook.onrender.com/api/v1/auth/me" \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'
```

---

## Job Management Endpoints

### Create a New Job (Upload PDF)
```bash
curl -X POST "https://pdf2audiobook.onrender.com/api/v1/jobs/" \
  -H "Authorization: Bearer <jwt-token>" \
  -F "file=@/path/to/your/document.pdf" \
  -F "voice_provider=openai" \
  -F "voice=alloy" \
  -F "reading_speed=1.0" \
  -F "include_summary=true"
```

### List User's Jobs
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/" \
  -H "Authorization: Bearer <jwt-token>"
```

### List Jobs with Pagination
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/?page=1&limit=10&status=completed" \
  -H "Authorization: Bearer <jwt-token>"
```

### Get Specific Job Details
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/123" \
  -H "Authorization: Bearer <jwt-token>"
```
*Replace `123` with actual job ID*

### Get Job Status (Lightweight)
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/123/status" \
  -H "Authorization: Bearer <jwt-token>"
```
*Replace `123` with actual job ID*

---

## Payment Endpoints

### Get Available Products
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/payments/products" \
  -H "Authorization: Bearer <jwt-token>"
```

### Create Checkout URL
```bash
curl -X POST "https://pdf2audiobook.onrender.com/api/v1/payments/checkout-url" \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prod_pro",
    "success_url": "https://yourapp.com/success",
    "cancel_url": "https://yourapp.com/cancel"
  }'
```

---

## Error Testing

### Test Rate Limiting
```bash
# Make multiple requests quickly
for i in {1..15}; do
  curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/" \
    -H "Authorization: Bearer <jwt-token>" &
done
```

### Test Invalid Token
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/auth/me" \
  -H "Authorization: Bearer invalid-token"
```

### Test Missing Authentication
```bash
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/"
```

---

## Complete Workflow Example

```bash
#!/bin/bash

# 1. Check health
curl -X GET "https://pdf2audiobook.onrender.com/health"

# 2. Get user profile (replace with real JWT)
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Get available products
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/payments/products" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Upload a PDF (replace with real file path)
curl -X POST "https://pdf2audiobook.onrender.com/api/v1/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@dummy.pdf" \
  -F "voice_provider=openai" \
  -F "voice=alloy" \
  -F "reading_speed=1.2"

# 5. List jobs
curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 6. Poll job status (replace JOB_ID with actual ID)
while true; do
  curl -X GET "https://pdf2audiobook.onrender.com/api/v1/jobs/JOB_ID/status" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN"
  sleep 5
done
```

---

## Notes

- **Rate Limits**: 10 job creations/minute, 100 general requests/minute per user
- **File Limits**: 50MB max PDF size
- **Authentication**: Required for all endpoints except `/health`
- **CORS**: Configured for frontend origins
- **SSL**: Automatic HTTPS enabled

Use these commands to test your deployed API. Replace `<jwt-token>` with actual Clerk JWT tokens and adjust file paths as needed.