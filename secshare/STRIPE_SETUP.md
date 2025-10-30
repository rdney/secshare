# Stripe Setup Guide

Configure billing from the start with this guide.

## 1. Create Stripe Account

1. Go to https://stripe.com and create an account
2. Complete your account setup

## 2. Get API Keys

1. Go to https://dashboard.stripe.com/apikeys
2. Copy your **Publishable key** and **Secret key**
3. For testing, use the test mode keys (starting with `pk_test_` and `sk_test_`)

## 3. Create Products and Prices

### Pro Plan ($19/month)

1. Go to https://dashboard.stripe.com/products
2. Click "Add product"
3. Name: "Pro Plan"
4. Description: "100 secrets/month, 10MB attachments"
5. Price: $19.00 USD
6. Billing period: Monthly
7. Save and copy the **Price ID** (starts with `price_`)

### Team Plan ($49/month)

1. Click "Add product"
2. Name: "Team Plan"
3. Description: "500 secrets/month, 50MB attachments, 5 users"
4. Price: $49.00 USD
5. Billing period: Monthly
6. Save and copy the **Price ID**

### Enterprise Plan (Custom)

For enterprise, you'll handle this through custom contracts and Stripe Invoices.

## 4. Set Up Webhooks

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://yourdomain.com/api/v1/subscriptions/webhook`
   - For local dev: Use ngrok or similar to expose localhost
   - Example: `https://abc123.ngrok.io/api/v1/subscriptions/webhook`
4. Description: "SecShare subscription events"
5. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
6. Add endpoint
7. Copy the **Signing secret** (starts with `whsec_`)

## 5. Configure Environment Variables

Add to your `backend/.env`:

\`\`\`bash
STRIPE_SECRET_KEY=sk_test_...your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_...your_webhook_secret
STRIPE_PRICE_ID_PRO=price_...your_pro_price_id
STRIPE_PRICE_ID_TEAM=price_...your_team_price_id
STRIPE_PRICE_ID_ENTERPRISE=price_...your_enterprise_price_id  # Optional
\`\`\`

Also add to root `.env` for Docker:

\`\`\`bash
SECRET_KEY=some-secure-random-key-here
STRIPE_SECRET_KEY=sk_test_...your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_...your_webhook_secret
STRIPE_PRICE_ID_PRO=price_...your_pro_price_id
STRIPE_PRICE_ID_TEAM=price_...your_team_price_id
\`\`\`

## 6. Test the Integration

### Test Checkout

1. Start the application
2. Register a new account
3. Go to Billing page
4. Click "Upgrade to Pro"
5. Use Stripe test card: `4242 4242 4242 4242`
6. Expiry: Any future date
7. CVC: Any 3 digits
8. Complete checkout

### Test Webhooks

1. After successful checkout, check your database
2. User's subscription should be updated to "PRO"
3. Stripe customer ID should be saved

### Test Billing Portal

1. Click "Manage Billing" button
2. Should redirect to Stripe Customer Portal
3. Test canceling/updating subscription

## 7. Go Live

When ready for production:

1. Switch from test mode to live mode in Stripe
2. Update `.env` with live API keys
3. Create live products and prices
4. Update webhook endpoint to production URL
5. Test thoroughly with real (small amount) transactions

## Webhook Testing with ngrok

For local development:

\`\`\`bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add webhook endpoint in Stripe: https://abc123.ngrok.io/api/v1/subscriptions/webhook
\`\`\`

## Troubleshooting

### Webhook not working
- Check the signing secret is correct
- Verify endpoint URL is accessible from internet
- Check Stripe dashboard > Webhooks for delivery attempts
- Review logs in Stripe dashboard

### Subscription not updating
- Verify webhook events are being received
- Check backend logs for errors
- Ensure database connection is working
- Verify price IDs match exactly

### Test Cards

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- 3D Secure: `4000 0025 0000 3155`

More test cards: https://stripe.com/docs/testing

## Free Plan Note

The free plan doesn't require Stripe - it's created automatically when users register. Only Pro, Team, and Enterprise plans need Stripe configuration.
