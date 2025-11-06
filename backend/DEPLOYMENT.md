# Backend Deployment Guide

This guide covers deploying the PDF2Audiobook FastAPI backend to production hosting services.

## Deployment Files

```
backend/
├── Dockerfile              # Multi-stage production build
├── railway.toml           # Railway deployment config
├── build.sh              # General build script (with migrations)
├── render-build.sh       # Render-specific build script (no migrations)
├── render-start.sh       # Render start script (with migrations)
├── Procfile              # Heroku process definition
├── runtime.txt           # Python version for Heroku
├── .env.example          # Environment variables template
└── DEPLOYMENT.md         # This deployment guide
```

## Supported Platforms

### 🚂 Railway (Recommended)

Railway provides excellent Python support with built-in PostgreSQL and Redis.

#### Deploy to Railway

1. **Connect Repository**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login and connect
   railway login
   railway link
   ```

2. **Set Environment Variables**
   ```bash
   railway variables set DATABASE_URL=postgresql://...
   railway variables set REDIS_URL=redis://...
   railway variables set SECRET_KEY=your-secret-key
   railway variables set CLERK_PEM_PUBLIC_KEY=your-clerk-key
   railway variables set AWS_ACCESS_KEY_ID=your-aws-key
   railway variables set AWS_SECRET_ACCESS_KEY=your-aws-secret
   railway variables set S3_BUCKET_NAME=your-bucket
   railway variables set PADDLE_VENDOR_ID=your-vendor-id
   railway variables set PADDLE_VENDOR_AUTH_CODE=your-auth-code
   railway variables set OPENAI_API_KEY=your-openai-key
   ```

3. **Deploy**
   ```bash
   railway up
   ```

4. **Database Setup**
   Railway provides managed PostgreSQL. Run migrations:
   ```bash
   railway run alembic upgrade head
   ```

### 🎨 Render

Render supports Docker deployments with persistent disks.

#### Deploy to Render

1. **Create Render Service**
   - Go to [render.com](https://render.com)
   - Create a new "Web Service"
   - Connect your GitHub repository
   - Choose build method: Docker (uses existing Dockerfile)

2. **Docker Build Settings**
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Context Directory**: `backend`

3. **Alternative: Native Python Build**
   If you prefer native Python deployment:
   - **Runtime**: Python 3
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `./render-start.sh`

4. **Environment Variables**
   Set these in Render dashboard:
   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   SECRET_KEY=your-secret-key
   CLERK_PEM_PUBLIC_KEY=your-clerk-key
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   S3_BUCKET_NAME=your-bucket
   PADDLE_VENDOR_ID=your-vendor-id
   PADDLE_VENDOR_AUTH_CODE=your-auth-code
   OPENAI_API_KEY=your-openai-key
   ENVIRONMENT=production
   ```

5. **Health Check**
   Render automatically detects the health check endpoint at `/health`

### 🟣 Heroku

Heroku has good Python support but requires more configuration.

#### Deploy to Heroku

1. **Create Heroku App**
   ```bash
   heroku create your-app-name
   ```

2. **Add Buildpacks**
   ```bash
   heroku buildpacks:add heroku/python
   ```

3. **Database Setup**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   heroku addons:create heroku-redis:hobby-dev
   ```

4. **Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set CLERK_PEM_PUBLIC_KEY=your-clerk-key
   # ... set all required variables
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **Run Migrations**
   ```bash
   heroku run alembic upgrade head
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `SECRET_KEY` | JWT signing key (256-bit) | `your-256-bit-secret-key` |
| `CLERK_PEM_PUBLIC_KEY` | Clerk public key for JWT verification | `-----BEGIN PUBLIC KEY-----...` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `your-secret-key` |
| `S3_BUCKET_NAME` | S3 bucket name | `pdf2audiobook-bucket` |
| `PADDLE_VENDOR_ID` | Paddle vendor ID | `12345` |
| `PADDLE_VENDOR_AUTH_CODE` | Paddle auth code | `your-auth-code` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Set to `production` for prod |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ALLOWED_HOSTS` | `http://localhost:3000` | CORS allowed origins |
| `AWS_REGION` | `us-east-1` | AWS region |
| `PADDLE_ENVIRONMENT` | `sandbox` | `sandbox` or `production` |

## Production Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] Database and Redis services provisioned
- [ ] AWS S3 bucket created with proper permissions
- [ ] Clerk application configured
- [ ] Paddle account set up
- [ ] OpenAI API key obtained

### Deployment Steps
- [ ] Code deployed successfully
- [ ] Database migrations applied
- [ ] Health check endpoint responding (`/health`)
- [ ] API documentation accessible (`/docs`)
- [ ] Worker processes running (if applicable)

### Post-Deployment
- [ ] Test authentication flow
- [ ] Test PDF upload and processing
- [ ] Verify payment integration
- [ ] Check monitoring and logging
- [ ] Set up domain and SSL (if needed)

## Monitoring & Maintenance

### Health Checks
The application includes a `/health` endpoint that checks:
- Database connectivity
- Redis connectivity
- Required services availability

### Logs
- Structured JSON logging in production
- Environment-specific log levels
- Request/response logging middleware

### Scaling
- Horizontal scaling supported via multiple workers
- Database connection pooling configured
- Redis for session and cache management

## Troubleshooting

### Common Issues

**Database Connection Failed**
- Check DATABASE_URL format
- Verify database credentials
- Ensure database is accessible from deployment environment

**Redis Connection Failed**
- Check REDIS_URL format
- Verify Redis service is running
- Check network connectivity

**Authentication Issues**
- Verify CLERK_PEM_PUBLIC_KEY is correct
- Check JWT token format
- Ensure Clerk application domains are configured

**File Upload Issues**
- Check AWS credentials
- Verify S3 bucket permissions
- Confirm bucket exists and is accessible

### Debug Commands

```bash
# Check application logs
railway logs

# Check database connectivity
railway run python -c "from app.core.database import SessionLocal; db = SessionLocal(); db.execute(text('SELECT 1')); print('DB OK')"

# Check Redis connectivity
railway run python -c "import redis; r = redis.from_url(os.getenv('REDIS_URL')); r.ping(); print('Redis OK')"

# Test API endpoints
curl -H "Authorization: Bearer <token>" https://your-api-url/health
```

## Security Considerations

- All secrets stored as environment variables
- No sensitive data logged
- CORS configured for allowed origins only
- Rate limiting enabled on all endpoints
- Input validation on all user inputs
- HTTPS enforced in production

## Performance Optimization

- Gzip compression enabled
- Database connection pooling
- Redis caching for sessions
- Optimized Docker images with multi-stage builds
- Worker processes for background tasks