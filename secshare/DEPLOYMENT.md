# Railway Deployment Guide

This guide walks you through deploying SecShare to Railway.

## Prerequisites

1. Railway account (https://railway.app)
2. GitHub account
3. Stripe account (for payments)

## Step 1: Push Code to GitHub

```bash
git push origin main
```

## Step 2: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your `secshare` repository
4. Railway will create a new project

## Step 3: Add Services

You need 4 services in your Railway project:

### A. PostgreSQL Database

1. In your Railway project, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway will provision the database and provide `DATABASE_URL`

### B. Redis Database

1. Click "+ New" again
2. Select "Database" → "Redis"
3. Railway will provision Redis and provide `REDIS_URL`

### C. Backend Service

1. Click "+ New" → "GitHub Repo"
2. Select your repository
3. Click "Add variables" and set:
   ```
   SECRET_KEY=<generate a random secret key>
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   CORS_ORIGINS=http://localhost:5173,https://<your-frontend-domain>.up.railway.app
   STRIPE_SECRET_KEY=<your stripe secret key>
   STRIPE_WEBHOOK_SECRET=<your stripe webhook secret>
   STRIPE_PRICE_ID_PRO=<your stripe pro price id>
   STRIPE_PRICE_ID_TEAM=price_your_team_price_id
   STRIPE_PRICE_ID_ENTERPRISE=price_your_enterprise_price_id
   ```
4. In Settings → "Root Directory", set to `backend`
5. Railway will auto-deploy using the Dockerfile

### D. Frontend Service

1. Click "+ New" → "GitHub Repo"
2. Select your repository again
3. In Settings:
   - Set "Root Directory" to `frontend`
   - Set "Build Command" to `npm install && npm run build`
   - Set "Start Command" to `npm run preview -- --host 0.0.0.0 --port $PORT`
4. Add variable:
   ```
   VITE_API_URL=https://<your-backend-domain>.up.railway.app
   ```

## Step 4: Configure Frontend API URL

1. Create `frontend/.env.production`:
   ```
   VITE_API_URL=https://<your-backend-domain>.up.railway.app
   ```
2. Update `frontend/src/lib/api.ts`:
   ```typescript
   const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
   ```

## Step 5: Update CORS Origins

Once you have your frontend URL:
1. Go to Backend service variables
2. Update `CORS_ORIGINS` to include your frontend domain:
   ```
   CORS_ORIGINS=https://<your-frontend-domain>.up.railway.app
   ```
3. Redeploy backend service

## Step 6: Run Database Migrations

1. In Railway, go to your Backend service
2. Open the "Deployments" tab
3. Click on the latest deployment
4. In the deployment logs, you should see Alembic migrations running automatically
5. If needed, you can run migrations manually in the Railway terminal:
   ```bash
   alembic upgrade head
   ```

## Step 7: Configure Stripe Webhook

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://<your-backend-domain>.up.railway.app/api/v1/subscriptions/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy the webhook secret
5. Update `STRIPE_WEBHOOK_SECRET` in Railway backend variables

## Step 8: Test Your Deployment

1. Visit your frontend URL: `https://<your-frontend-domain>.up.railway.app`
2. Register a new account
3. Create a secret
4. Test the checkout flow
5. Verify webhooks are working in Stripe dashboard

## Environment Variables Reference

### Backend (.env)
- `SECRET_KEY` - Random secret for JWT tokens (generate with `openssl rand -hex 32`)
- `DATABASE_URL` - Provided by Railway PostgreSQL
- `REDIS_URL` - Provided by Railway Redis
- `CORS_ORIGINS` - Your frontend domain(s)
- `STRIPE_SECRET_KEY` - From Stripe dashboard (test or live)
- `STRIPE_WEBHOOK_SECRET` - From Stripe webhook configuration
- `STRIPE_PRICE_ID_PRO` - Stripe price ID for Pro plan
- `STRIPE_PRICE_ID_TEAM` - Stripe price ID for Team plan (optional)
- `STRIPE_PRICE_ID_ENTERPRISE` - Stripe price ID for Enterprise plan (optional)

### Frontend (.env.production)
- `VITE_API_URL` - Your backend Railway URL

## Troubleshooting

### Backend won't start
- Check that DATABASE_URL and REDIS_URL are correctly set
- Verify migrations ran successfully in deployment logs
- Check backend logs for errors

### Frontend can't connect to backend
- Verify VITE_API_URL is set correctly
- Check CORS_ORIGINS includes your frontend domain
- Rebuild frontend after changing env vars

### Stripe webhooks failing
- Verify webhook URL matches your backend domain
- Check STRIPE_WEBHOOK_SECRET is correct
- View webhook logs in Stripe dashboard

## Cost Estimate

Railway pricing:
- $5/month free credit (with account)
- Backend: ~$5-10/month
- Frontend: ~$5/month
- PostgreSQL: Included in usage
- Redis: Included in usage

Total: ~$5-15/month (depending on usage)

## Custom Domain (Optional)

1. Go to Frontend service settings
2. Click "Settings" → "Domains"
3. Click "Custom Domain"
4. Add your domain and configure DNS
5. Repeat for backend if needed
6. Update CORS_ORIGINS and VITE_API_URL accordingly
