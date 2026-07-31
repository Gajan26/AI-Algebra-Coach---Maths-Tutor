# Deployment Guide: AI Algebra Coach

This guide covers deploying AI Algebra Coach to production environments. Choose the deployment option that best fits your infrastructure preferences and budget.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Option 1: Vercel + Railway](#option-1-vercel--railway-recommended)
3. [Option 2: Vercel + Render](#option-2-vercel--render)
4. [Option 3: AWS ECS/Fargate](#option-3-aws-ecsfargate)
5. [Option 4: Self-Hosted with Docker](#option-4-self-hosted-with-docker)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] Create a separate Anthropic API key for production
- [ ] Set up billing alerts in [Anthropic Console](https://console.anthropic.com/account/billing/overview)
- [ ] Add authentication/rate limiting to prevent abuse
- [ ] Configure CORS properly (no wildcards)
- [ ] Set up logging and monitoring
- [ ] Test image upload and coaching flow end-to-end
- [ ] Review security best practices below
- [ ] Implement database backups (if using database)
- [ ] Set up automated health checks

### Security Best Practices

**API Key Management:**
```bash
# Never commit .env files
# Use environment secrets in your deployment platform
# Rotate keys periodically
# Use separate keys for dev/prod
```

**CORS Configuration:**
```bash
# Development (allows localhost)
CORS_ORIGINS=http://localhost:3000

# Production (specific domain only)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Rate Limiting:**
Add rate limiting to prevent abuse:
```python
# backend/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/vision/process")
@limiter.limit("30/hour")  # 30 requests per hour per IP
async def process_vision(image: UploadFile = File(...)):
    ...
```

---

## Option 1: Vercel + Railway (Recommended)

This is the easiest option for most users: Vercel for frontend, Railway for backend.

### Costs
- **Vercel:** Free tier available, ~$20/month for production
- **Railway:** ~$5/month for basic backend + API costs
- **Anthropic API:** Based on usage (~$0.05–$0.15 per interaction)

### Setup

#### Step 1: Prepare repositories

Split into two repositories (recommended for easier deployment):

```bash
# Create backend repo
git clone <your-repo>
cd AI Algebra Coach
mkdir algebra-coach-backend
cp -r backend/* algebra-coach-backend/
cd algebra-coach-backend
git init
git add .
git commit -m "Initial backend deployment"
git push -u origin main

# Create frontend repo
cd ../frontend
git init
git add .
git commit -m "Initial frontend deployment"
git push -u origin main
```

#### Step 2: Deploy backend to Railway

1. Go to [railway.app](https://railway.app) and sign up
2. Click "New Project" → "GitHub Repo"
3. Select your `algebra-coach-backend` repo
4. Railway auto-detects Python + FastAPI
5. Add environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY`: Your API key
   - `CORS_ORIGINS`: `https://yourdomain.com`
   - `ENVIRONMENT`: `production`
6. Deploy (automatic on git push)

Get your backend URL from Railway dashboard (looks like `https://algebra-coach-backend-prod.railway.app`)

#### Step 3: Deploy frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up with GitHub
2. Click "New Project" → select your `frontend` repo
3. Configure build settings:
   - Framework: Next.js
   - Root Directory: `./`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your Railway backend URL
5. Deploy (automatic on git push)

#### Step 4: Update Railway CORS

Back in Railway dashboard, update backend environment:
```
CORS_ORIGINS=https://yourdomain.vercel.app
```

Your app is now live! 🎉

---

## Option 2: Vercel + Render

Similar to Railway but using Render for the backend.

### Costs
- **Vercel:** ~$20/month
- **Render:** Free tier (may be slow), $7/month for production
- **Anthropic API:** Based on usage

### Setup

#### Step 1: Deploy backend to Render

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub `algebra-coach-backend` repo
4. Configure:
   - **Name:** `algebra-coach-backend`
   - **Environment:** Python 3.11
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 8000`
   - **Instance Type:** Starter (free) or Standard ($7/month)
5. Add environment variables:
   - `ANTHROPIC_API_KEY`: Your API key
   - `CORS_ORIGINS`: Leave blank for now
   - `ENVIRONMENT`: `production`
6. Deploy

Get your backend URL from Render (looks like `https://algebra-coach-backend.onrender.com`)

#### Step 2: Deploy frontend to Vercel

Same as Option 1, Step 3

#### Step 3: Update Render CORS

Back in Render dashboard, update environment:
```
CORS_ORIGINS=https://yourdomain.vercel.app
```

---

## Option 3: AWS ECS/Fargate

For teams wanting AWS infrastructure.

### Costs
- **ECS Fargate:** ~$15–30/month
- **Application Load Balancer:** ~$15/month
- **Data Transfer:** $0.09/GB
- **Anthropic API:** Based on usage

### Architecture

```
Route 53 (DNS)
  ↓
Application Load Balancer
  ├→ ECS Fargate Backend (algebra-coach-api)
  └→ S3 + CloudFront (frontend static files)
```

### Setup

#### Step 1: Prepare AWS environment

```bash
# Install AWS CLI and configure
aws configure

# Create ECR repositories
aws ecr create-repository --repository-name algebra-coach-backend --region us-east-1
aws ecr create-repository --repository-name algebra-coach-frontend --region us-east-1
```

#### Step 2: Build and push Docker images

```bash
# Backend
cd backend
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker build -t algebra-coach-backend:latest .
docker tag algebra-coach-backend:latest \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/algebra-coach-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/algebra-coach-backend:latest

# Frontend
cd ../frontend
docker build -t algebra-coach-frontend:latest .
docker tag algebra-coach-frontend:latest \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/algebra-coach-frontend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/algebra-coach-frontend:latest
```

#### Step 3: Create ECS task definitions

Use AWS Console or CDK to create:
- Task definition for backend (CPU: 256, Memory: 512)
- Task definition for frontend (CPU: 256, Memory: 512)

Set environment variables in task definitions via `containerDefinitions`.

#### Step 4: Create ECS services

- Backend service with load balancer
- Frontend service (or use S3 + CloudFront for static files)

#### Step 5: Configure DNS

Create Route 53 A record pointing to Application Load Balancer.

---

## Option 4: Self-Hosted with Docker

For maximum control, deploy on your own server.

### Requirements
- Server with Docker + Docker Compose
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)

### Setup

#### Step 1: Prepare server

```bash
# SSH into your server
ssh user@your-server-ip

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repository
git clone <your-repo>
cd AI\ Algebra\ Coach
```

#### Step 2: Configure environment

```bash
# Create production environment file
cat > backend/.env << EOF
ANTHROPIC_API_KEY=your-api-key
CORS_ORIGINS=https://yourdomain.com
ENVIRONMENT=production
VISION_MODEL=claude-3-5-sonnet-20241022
COACH_MODEL=claude-3-5-sonnet-20241022
EOF

cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
EOF
```

#### Step 3: Use Nginx as reverse proxy

Create `nginx.conf`:

```nginx
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### Step 4: Update docker-compose.yml for production

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - backend
      - frontend

  backend:
    build:
      context: ./backend
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CORS_ORIGINS=https://yourdomain.com
      - ENVIRONMENT=production
    restart: always

  frontend:
    build:
      context: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://yourdomain.com/api
    restart: always
```

#### Step 5: Start services

```bash
# Set up SSL with Let's Encrypt (Certbot)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Start Docker services
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f
```

---

## Environment Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `VISION_MODEL` | `claude-3-5-sonnet-20241022` | Model for image transcription |
| `COACH_MODEL` | `claude-3-5-sonnet-20241022` | Model for Socratic feedback |
| `ENVIRONMENT` | `development` | Set to `production` for prod |

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

---

## Monitoring & Logging

### Application Logs

**Vercel (frontend):**
- View in [vercel.com](https://vercel.com) → Project → Deployments → Logs

**Railway (backend):**
- View in Railway dashboard → Logs tab

**Render (backend):**
- View in Render dashboard → Logs

### Error Tracking

Add error monitoring with Sentry:

```bash
# Install Sentry
pip install sentry-sdk

# Add to backend/main.py
import sentry_sdk
sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    environment="production",
)
```

### Cost Monitoring

Set up spending alerts in Anthropic Console:

1. Go to [console.anthropic.com](https://console.anthropic.com/account/billing/overview)
2. Click "Spending Limits"
3. Set alert when spending reaches 50%, 80%, 100%

### Performance Monitoring

Monitor these metrics:
- API response time (target: < 10s for image processing)
- WebSocket connection uptime (target: 99.9%)
- API error rate (target: < 1%)
- Budget usage vs. forecasted

---

## Troubleshooting

### Backend won't start

**Error:** `ANTHROPIC_API_KEY is not configured`

```bash
# Solution: Set environment variable in deployment platform
# Vercel: Settings → Environment Variables
# Railway: Variables tab
# Render: Environment tab
```

### WebSocket fails to connect

**Error:** WebSocket connection fails in browser

```bash
# Check CORS_ORIGINS includes your domain:
CORS_ORIGINS=https://yourdomain.com

# For local testing:
CORS_ORIGINS=http://localhost:3000

# Ensure backend is accessible:
curl https://api.yourdomain.com/docs
```

### Image processing times out

**Symptom:** "Reading your work..." shows for > 30 seconds

```bash
# Solution: Increase FastAPI timeout or client-side timeout
# In frontend/app/page.tsx:
const response = await fetch(`${API_URL}/api/vision/process`, {
  method: "POST",
  body,
  signal: AbortSignal.timeout(60000), // 60 second timeout
});
```

### High API costs

**Symptom:** Unexpected high spending on Anthropic API

1. Check usage in [console.anthropic.com](https://console.anthropic.com/account/usage)
2. Enable request logging to track usage
3. Consider implementing caching for identical images
4. Add rate limiting per user

### Database connection errors

If you add PostgreSQL later:

```bash
# Check connection string
DATABASE_URL=postgresql://user:password@db.example.com:5432/algebra

# Run migrations
alembic upgrade head
```

---

## Next Steps

1. Test end-to-end in production
2. Set up monitoring and alerts
3. Configure database backups
4. Plan for scaling (if needed)
5. Regular security audits

For support, check [Anthropic API documentation](https://docs.anthropic.com) or your platform's support team.

---

**Last updated:** 2025-07-31
