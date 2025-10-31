# Railway CLI Deployment Guide

Quick deployment using Railway CLI.

## Step 1: Login

```bash
railway login
```

This will open a browser for authentication.

## Step 2: Create Project and Link

```bash
cd /Users/rodney/Projects/secshare
railway init
```

Select "Create new project" and name it `secshare`.

## Step 3: Add PostgreSQL

```bash
railway add --database postgres
```

## Step 4: Add Redis

```bash
railway add --database redis
```

## Step 5: Deploy Backend

```bash
cd backend
railway up
```

Railway will detect the Dockerfile and deploy it.

## Step 6: Set Backend Environment Variables

```bash
railway variables set SECRET_KEY=$(openssl rand -hex 32)
railway variables set STRIPE_SECRET_KEY=<your-stripe-secret-key>
railway variables set STRIPE_WEBHOOK_SECRET=<your-webhook-secret>
railway variables set STRIPE_PRICE_ID_PRO=<your-pro-price-id>
railway variables set STRIPE_PRICE_ID_TEAM=<your-team-price-id>
railway variables set STRIPE_PRICE_ID_ENTERPRISE=<your-enterprise-price-id>
railway variables set CORS_ORIGINS=http://localhost:5173
```

## Step 7: Get Backend URL

```bash
railway domain
```

Copy the URL (e.g., `https://secshare-backend.up.railway.app`)

## Step 8: Create Frontend Service

```bash
cd ../frontend
railway service create frontend
railway link
```

## Step 9: Set Frontend Environment Variables

```bash
railway variables set VITE_API_URL=https://<your-backend-url>.up.railway.app
```

## Step 10: Deploy Frontend

```bash
railway up
```

## Step 11: Get Frontend URL

```bash
railway domain
```

## Step 12: Update Backend CORS

```bash
cd ../backend
railway variables set CORS_ORIGINS=https://<your-frontend-url>.up.railway.app,http://localhost:5173
```

## Step 13: Redeploy Backend

```bash
railway up
```

## Alternative: One-liner Setup

After `railway init`, you can use:

```bash
# Add databases
railway add -d postgres && railway add -d redis

# Set all variables at once (backend)
cd backend
railway variables set \
  SECRET_KEY=$(openssl rand -hex 32) \
  STRIPE_SECRET_KEY=<your-stripe-secret-key> \
  STRIPE_WEBHOOK_SECRET=<your-webhook-secret> \
  STRIPE_PRICE_ID_PRO=<your-pro-price-id>

# Deploy
railway up
```

## Useful Commands

```bash
# View logs
railway logs

# Open dashboard
railway open

# Check status
railway status

# List variables
railway variables

# Connect to database
railway connect postgres

# Run migrations
railway run alembic upgrade head
```

## Note

After deployment, update your Stripe webhook URL to:
`https://<your-backend-url>.up.railway.app/api/v1/subscriptions/webhook`
