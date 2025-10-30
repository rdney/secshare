# SecShare - Secure Secret Sharing Platform

Secure secret sharing with automatic expiration, view limits, and subscription management.

## Features

- **Secure Secret Sharing**: AES-256-GCM encryption for all secrets
- **Automatic Expiration**: Time-based and view-count-based expiration
- **Access Logs**: Track when and from where secrets are accessed
- **Subscription Plans**: Free, Pro, Team, and Enterprise tiers
- **Stripe Integration**: Complete billing management
- **Team Management**: Collaborate with your team members
- **File Attachments**: Share files securely (Pro+ plans)

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic (migrations)
- Redis (caching/sessions)
- Stripe (payments)

### Frontend
- React 18
- TypeScript
- Vite
- TailwindCSS
- Zustand (state management)
- React Router

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Stripe account for billing features

### 1. Clone and Setup

\`\`\`bash
git clone <repo-url>
cd secshare
\`\`\`

### 2. Configure Environment

\`\`\`bash
cd backend
cp .env.example .env
# Edit .env with your settings, especially Stripe keys
\`\`\`

### 3. Start Services

\`\`\`bash
docker-compose up -d
\`\`\`

### 4. Run Database Migrations

\`\`\`bash
docker-compose exec backend alembic upgrade head
\`\`\`

### 5. Access Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Development Setup

### Backend

\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
\`\`\`

### Frontend

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

## Stripe Configuration

1. Create a Stripe account at https://stripe.com
2. Get your API keys from https://dashboard.stripe.com/apikeys
3. Create products and prices for Pro, Team, and Enterprise plans
4. Set up webhook endpoint: `https://yourdomain.com/api/v1/subscriptions/webhook`
5. Add webhook events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

## Subscription Plans

| Plan | Secrets/Month | Attachments | Team Size | Price |
|------|--------------|-------------|-----------|-------|
| Free | 10 | No | 1 | $0 |
| Pro | 100 | 10MB | 1 | $19 |
| Team | 500 | 50MB | 5 | $49 |
| Enterprise | Unlimited | Custom | Unlimited | Custom |

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Secrets
- `POST /api/v1/secrets` - Create secret
- `GET /api/v1/secrets/{id}` - Retrieve secret
- `GET /api/v1/secrets` - List user's secrets
- `DELETE /api/v1/secrets/{id}` - Delete secret
- `GET /api/v1/secrets/{id}/logs` - Get access logs

### Subscriptions
- `GET /api/v1/subscriptions/me` - Get subscription
- `GET /api/v1/subscriptions/usage` - Get usage stats
- `POST /api/v1/subscriptions/checkout` - Create checkout session
- `POST /api/v1/subscriptions/portal` - Access billing portal
- `POST /api/v1/subscriptions/webhook` - Stripe webhook

### Teams
- `POST /api/v1/teams` - Create team
- `GET /api/v1/teams/me` - Get user's team
- `GET /api/v1/teams/{id}/members` - List team members

## Security

- All secrets encrypted with AES-256-GCM
- Unique encryption key per secret
- Master key encryption for secret keys
- HTTPS required in production
- JWT authentication
- CORS protection
- SQL injection protection (SQLAlchemy)

## Deployment

### Production Checklist

1. Set strong `SECRET_KEY` in backend .env
2. Use production Stripe keys
3. Configure proper CORS origins
4. Set up SSL/TLS certificates
5. Use production database (not dev credentials)
6. Enable database backups
7. Set up monitoring and logging
8. Configure rate limiting
9. Review security headers

### Environment Variables

See `backend/.env.example` for all available configuration options.

## License

Proprietary - All rights reserved

## Support

For issues and questions:
- GitHub Issues: <repo-url>/issues
- Email: support@secshare.com
