# SecShare - Quick Start Guide

Get up and running in 5 minutes.

## Prerequisites

- Docker & Docker Compose installed
- Stripe account (for billing features)

## Setup Steps

### 1. Configure Stripe

Before starting the app, set up Stripe:

1. Create account at https://stripe.com
2. Go to https://dashboard.stripe.com/apikeys
3. Copy your test API keys
4. Create products for Pro ($19) and Team ($49) plans
5. Copy the price IDs

See `STRIPE_SETUP.md` for detailed instructions.

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Stripe keys
nano .env  # or use your preferred editor
```

Add:
```bash
SECRET_KEY=your-random-secret-key-here
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
STRIPE_PRICE_ID_PRO=price_your_pro_id
STRIPE_PRICE_ID_TEAM=price_your_team_id
```

### 3. Start Application

```bash
# Run setup script
./setup.sh

# Or manually:
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### 4. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Create First Account

1. Go to http://localhost:5173/register
2. Enter email and password
3. Login and create your first secret!

## Basic Usage

### Create a Secret

1. Click "New Secret"
2. Enter secret content
3. Set expiration (default 24 hours)
4. Set max views (default 1)
5. Click "Create Secret"
6. Copy the generated link
7. Share securely

### Share a Secret

Send the link to recipient:
```
http://localhost:5173/s/abc123xyz
```

- Link expires after time limit OR max views
- Recipient clicks link to reveal secret
- Secret is destroyed after max views reached

### View Access Logs

1. Go to Dashboard
2. Click eye icon on any secret
3. See who accessed it, when, and from where

### Upgrade Plan

1. Click "Billing" in nav
2. Choose Pro or Team plan
3. Complete checkout with Stripe
4. Use test card: 4242 4242 4242 4242

## Development

### Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

### Database Commands

```bash
# Create migration
npm run db:migrate "add new field"

# Run migrations
npm run db:upgrade

# Rollback migration
npm run db:downgrade
```

## Testing Stripe

### Test Cards
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Use any future expiry date and any CVC

### Webhook Testing (Local)

Install ngrok:
```bash
brew install ngrok
ngrok http 8000
```

Use the ngrok HTTPS URL for Stripe webhooks:
```
https://abc123.ngrok.io/api/v1/subscriptions/webhook
```

## Common Issues

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart services
docker-compose restart postgres backend
```

### Frontend Can't Connect to Backend
- Check backend is running: http://localhost:8000/health
- Check CORS settings in `backend/app/core/config.py`

### Stripe Webhook Not Working
- For local dev, use ngrok
- Check webhook signing secret matches
- Verify endpoint URL is correct in Stripe dashboard

## Next Steps

1. Read `STRIPE_SETUP.md` for production Stripe setup
2. Review `ARCHITECTURE.md` for system design
3. Check `README.md` for full documentation
4. Configure production environment variables
5. Set up monitoring and logging

## Support

- Documentation: See README.md and other .md files
- Issues: Create GitHub issue
- Questions: support@secshare.com
