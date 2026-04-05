# ServerRoot.net Web Interface - Deployment Guide

## 📋 Prerequisites

### System Requirements

- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **RAM**: Minimum 2GB (4GB recommended)
- **Disk Space**: 500MB for installation
- **OS**: Linux, macOS, or Windows

### Optional Requirements

- **Domain**: Custom domain name production
- **SSL Certificate**: For HTTPS (recommended)
- **Reverse Proxy**: Nginx or Apache (recommended for production)
- **Load Balancer**: For high availability setups

## 🚀 Deployment Options

### Option 1: Quick Start - Development Mode

Perfect for testing and evaluation:

```bash
# Navigate to the web interface directory
cd /workspace/web/serverroot-ui

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

### Option 2: Production Build

For optimal performance in production:

```bash
# Build the application
npm run build

# Start production server
npm start

# Access at http://localhost:3000
```

### Option 3: Docker Deployment (Recommended)

Create a `Dockerfile`:

```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Production
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

EXPOSE 3000

CMD ["npm", "start"]
```

Build and run:

```bash
# Build Docker image
docker build -t serverroot-ui .

# Run container
docker run -p 3000:3000 serverroot-ui
```

### Option 4: Docker Compose (Full Stack)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://localhost:8443
    depends_on:
      - backend

  backend:
    image: serverroot-backend:latest
    ports:
      - "8443:8443"
    volumes:
      - ./data:/app/data
```

Run with:

```bash
docker-compose up -d
```

### Option 5: Cloud Platform Deployment

#### Vercel (Recommended for Next.js)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

#### AWS

Option A: AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init

# Deploy
eb deploy
```

Option B: AWS Amplify

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

#### Google Cloud Platform

```bash
# Install Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Deploy to Cloud Run
gcloud run deploy serverroot-ui \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure

```bash
# Install Azure CLI
# https://docs.microsoft.com/cli/azure/install-azure-cli

# Deploy to Azure Static Web Apps
az staticwebapp create \
  -g serverroot-rg \
  -n serverroot-ui \
  -s https://github.com/yourorg/serverroot \
  -b main \
  -o serverroot-ui
```

## 🔧 Configuration

### Environment Variables

Create `.env.local` for local development:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8443
NEXT_PUBLIC_WS_URL=ws://localhost:8443

# Feature Flags
NEXT_PUBLIC_ENABLE_AI_RESEARCH=true
NEXT_PUBLIC_ENABLE_REALTIME_UPDATES=true
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true

# Authentication (Future)
NEXT_PUBLIC_AUTH_ENABLED=false

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=UA-XXXXXXXXX-X
```

Production environment (`.env.production`):

```env
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.serverroot.net
NEXT_PUBLIC_WS_URL=wss://api.serverroot.net
```

### Next.js Configuration

Update `next.config.js` for production:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compress: true,
  poweredByHeader: false,
  
  // Environment-specific API rewrites
  async rewrites() {
    if (process.env.NODE_ENV === 'production') {
      return [
        {
          source: '/api/:path*',
          destination: process.env.NEXT_PUBLIC_API_URL + '/api/:path*',
        },
      ]
    }
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8443/api/:path*',
      },
    ]
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
```

## 🔐 SSL/TLS Configuration

### Using Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d serverroot.net

# Auto-renewal is configured automatically
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name serverroot.net;

    ssl_certificate /etc/letsencrypt/live/serverroot.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/serverroot.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
}
```

## 📊 Monitoring and Logging

### Application Monitoring

Add monitoring with Sentry:

```bash
npm install @sentry/nextjs
npx @sentry/wizard -i nextjs
```

### Performance Monitoring

Use Next.js Analytics:

```bash
npm install @vercel/analytics
```

Add to `app/layout.tsx`:

```typescript
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy ServerRoot UI

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build
      
      - name: Deploy
        run: |
          # Add your deployment command
      env:
        NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}
```

## 🧪 Testing

### Unit Tests

```bash
# Install testing dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# Run tests
npm test
```

### E2E Tests

```bash
# Install Playwright
npm install -D @playwright/test

# Run E2E tests
npx playwright test
```

## 📦 Build Optimization

### Analyze Bundle Size

```bash
# Install analyzer
npm install @next/bundle-analyzer

# Run build with analysis
ANALYZE=true npm run build
```

### Optimize Images

Add to `next.config.js`:

```javascript
module.exports = {
  images: {
    domains: ['serverroot.net'],
    formats: ['image/avif', 'image/webp'],
  },
}
```

## 🚨 Troubleshooting

### Build Failures

```bash
# Clean build cache
rm -rf .next node_modules
npm install
npm run build
```

### Memory Issues

Increase Node.js memory:

```bash
export NODE_OPTIONS=--max_old_space_size=4096
npm run build
```

### Production Issues

Check logs:

```bash
# PM2 logs
pm2 logs serverroot-ui

# Docker logs
docker logs serverroot-ui
```

## 📈 Scaling

### Horizontal Scaling

Use a load balancer with multiple instances:

```yaml
# docker-compose.yml
services:
  web:
    image: serverroot-ui
    deploy:
      replicas: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Database Scaling

For production, use:
- PostgreSQL or MongoDB for persistent data
- Redis for caching and session management
- Elasticsearch for search functionality

## 🔒 Security Best Practices

1. **Use HTTPS only** - Redirect HTTP to HTTPS
2. **Implement rate limiting** - Prevent abuse
3. **Use environment variables** - Never commit secrets
4. **Regular security updates** - Keep dependencies updated
5. **Implement authentication** - Add user authentication
6. **CORS configuration** - Restrict cross-origin requests
7. **Input validation** - Validate all user inputs
8. **Regular audits** - Run security audits

## 📞 Support

For deployment issues:
- 📧 Email: support@serverroot.net
- 📚 Docs: https://docs.serverroot.net
- 🐛 Issues: https://github.com/serverrootnet/issues

---

**Deploy ServerRoot.net web interface with confidence using this comprehensive guide!** 🚀🛡️