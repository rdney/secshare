# SecShare Architecture

## System Overview

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser   │◄───────►│   React      │◄───────►│   FastAPI    │
│             │  HTTPS  │   Frontend   │   REST  │   Backend    │
└─────────────┘         └──────────────┘         └──────┬───────┘
                                                          │
                        ┌─────────────────────────────────┼───────┐
                        │                                 │       │
                        ▼                                 ▼       ▼
                 ┌─────────────┐                  ┌──────────┐  ┌────────┐
                 │   Stripe    │                  │PostgreSQL│  │ Redis  │
                 │   Billing   │                  │          │  │        │
                 └─────────────┘                  └──────────┘  └────────┘
```

## Components

### Frontend (React + TypeScript)
- **Framework**: React 18 with Vite
- **Styling**: TailwindCSS (Heroku-inspired purple theme)
- **State Management**: Zustand
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Features**:
  - User authentication (login/register)
  - Secret creation with expiration settings
  - Dashboard with secret list
  - Access log viewing
  - Billing/subscription management
  - Responsive design

### Backend (Python + FastAPI)
- **Framework**: FastAPI (async Python web framework)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Encryption**: AES-256-GCM (cryptography)
- **API Structure**:
  - `/api/v1/auth` - Authentication endpoints
  - `/api/v1/secrets` - Secret management
  - `/api/v1/subscriptions` - Billing and usage
  - `/api/v1/teams` - Team management

### Database (PostgreSQL)
```
users
├── id (PK)
├── email (unique)
├── password_hash
├── team_id (FK)
└── timestamps

teams
├── id (PK)
├── name
├── slug (unique)
├── owner_id (FK)
└── timestamps

subscriptions
├── id (PK)
├── user_id (FK, unique)
├── team_id (FK, unique)
├── plan (enum)
├── status (enum)
├── stripe_customer_id
├── stripe_subscription_id
└── timestamps

secrets
├── id (PK)
├── encrypted_content
├── encrypted_key
├── iv
├── max_views
├── current_views
├── expires_at
├── created_by_id (FK)
├── team_id (FK)
└── timestamps

access_logs
├── id (PK)
├── secret_id (FK)
├── ip_address
├── user_agent
└── accessed_at

usage_stats
├── id (PK)
├── user_id (FK)
├── secrets_created_this_month
├── secret_requests_this_month
├── attachment_bytes_this_month
├── period_start
└── period_end
```

### Cache/Session (Redis)
- Session storage
- Rate limiting data
- Temporary data caching

### Payment Processing (Stripe)
- Subscription management
- Checkout sessions
- Customer portal
- Webhook handling
- Invoice generation

## Security Architecture

### Secret Encryption Flow

```
1. User creates secret with content "Hello World"

2. Backend generates:
   - Random 256-bit key (K)
   - Random 96-bit IV

3. Encrypt content:
   content_encrypted = AES-GCM(content, K, IV)

4. Encrypt the key:
   K_encrypted = AES-GCM(K, MASTER_KEY, IV_master)

5. Store in database:
   - content_encrypted (base64)
   - K_encrypted (base64)
   - IV (base64)

6. Secret retrieval:
   - Decrypt K: K = AES-GCM-decrypt(K_encrypted, MASTER_KEY)
   - Decrypt content: content = AES-GCM-decrypt(content_encrypted, K, IV)
   - Return to user
   - Increment view counter
   - Delete if max_views reached or expired
```

### Authentication Flow

```
1. User Registration:
   - Hash password with bcrypt
   - Create user record
   - Create free subscription
   - Initialize usage stats

2. User Login:
   - Verify email + password
   - Generate JWT token (30min expiry)
   - Return token to client

3. Authenticated Requests:
   - Client sends: Authorization: Bearer <token>
   - Backend validates JWT
   - Extract user_id from token
   - Load user from database
   - Process request
```

## Data Flow

### Create Secret
```
Frontend                Backend                 Database
   │                       │                        │
   ├─POST /secrets────────►│                        │
   │  {content, maxViews}  │                        │
   │                       ├─Check usage limits────►│
   │                       │◄─────Usage OK──────────┤
   │                       │                        │
   │                       ├─Generate key, IV       │
   │                       ├─Encrypt content        │
   │                       ├─Encrypt key            │
   │                       │                        │
   │                       ├─INSERT secret─────────►│
   │                       ├─UPDATE usage_stats────►│
   │◄────Secret created────┤◄─────────OK────────────┤
   │  {id, expires_at}     │                        │
```

### View Secret
```
Browser                 Backend                 Database
   │                       │                        │
   ├─GET /s/{id}──────────►│                        │
   │                       ├─SELECT secret─────────►│
   │                       │◄────Secret data────────┤
   │                       │                        │
   │                       ├─Check expiration       │
   │                       ├─Check max views        │
   │                       ├─Decrypt key            │
   │                       ├─Decrypt content        │
   │                       │                        │
   │                       ├─INSERT access_log─────►│
   │                       ├─UPDATE current_views──►│
   │◄────Secret content────┤                        │
   │  {content, views}     │                        │
```

### Subscription Upgrade
```
Frontend                Backend                 Stripe
   │                       │                        │
   ├─POST /checkout───────►│                        │
   │  {price_id}           │                        │
   │                       ├─Create customer───────►│
   │                       │◄──customer_id──────────┤
   │                       │                        │
   │                       ├─Create session────────►│
   │◄─────checkout_url─────┤◄──session_url──────────┤
   │                       │                        │
   ├─Redirect to Stripe───►│                        │
   │                       │                        │
   │ [User completes payment in Stripe]             │
   │                       │                        │
   │                       │◄─Webhook: completed────┤
   │                       ├─UPDATE subscription────►│
   │                       │  (plan=PRO, active)    │
```

## Deployment Architecture

### Docker Compose (Development)
```
├── postgres:5432
├── redis:6379
├── backend:8000
└── frontend:5173
```

### Production (Recommended)
```
┌──────────────────────────────────────┐
│           Load Balancer              │
│         (HTTPS termination)          │
└──────────┬───────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────┐
│Backend │   │Backend │  (Multiple instances)
│  Pod   │   │  Pod   │
└───┬────┘   └───┬────┘
    │            │
    └──────┬─────┘
           │
    ┌──────▼──────────────┐
    │   PostgreSQL        │
    │   (RDS/Managed)     │
    └─────────────────────┘
           │
    ┌──────▼──────────────┐
    │   Redis             │
    │   (ElastiCache)     │
    └─────────────────────┘

Static Frontend → CDN (Vercel/Netlify)
```

## Scalability Considerations

### Horizontal Scaling
- Stateless backend API (scales easily)
- Redis for shared session state
- Database connection pooling
- Load balancer for distribution

### Vertical Scaling
- Increase database resources for more concurrent connections
- Redis memory for caching
- CPU for encryption operations

### Performance Optimizations
- Database indexes on frequently queried fields
- Redis caching for user sessions
- CDN for frontend static assets
- Lazy loading in frontend
- Pagination for secret lists
- Background jobs for cleanup (expired secrets)

## Monitoring & Observability

### Metrics to Track
- API response times
- Database query performance
- Secret creation/retrieval rates
- Failed login attempts
- Stripe webhook failures
- Active subscriptions by tier
- Storage usage

### Logging
- Structured logging (JSON)
- Request/response logging
- Error tracking
- Audit logs for sensitive operations

### Health Checks
- `/health` endpoint
- Database connectivity
- Redis connectivity
- Stripe API availability
