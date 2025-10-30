from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import stripe
from app.db.base import get_db
from app.schemas.subscription import SubscriptionResponse, CreateCheckoutSession, UsageResponse
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.usage_stats import UsageStats
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get("/me", response_model=SubscriptionResponse)
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    return subscription


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime, timezone

    usage = db.query(UsageStats).filter(UsageStats.user_id == current_user.id).first()
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()

    # Reset usage on 1st of month (only for free plan)
    is_free_plan = not subscription or subscription.plan == SubscriptionPlan.FREE
    if is_free_plan and usage:
        now = datetime.now(timezone.utc)
        if now >= usage.period_end:
            # Calculate new period (1st of current month to 1st of next month)
            period_start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)

            # Calculate first day of next month
            if now.month == 12:
                period_end = datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            else:
                period_end = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)

            # Reset counters
            usage.secrets_created_this_month = 0
            usage.secret_requests_this_month = 0
            usage.attachment_bytes_this_month = 0
            usage.period_start = period_start
            usage.period_end = period_end
            db.commit()

    if not subscription:
        limit_secrets = settings.FREE_SECRETS_PER_MONTH
        limit_attachments = settings.FREE_MAX_ATTACHMENT_SIZE
        limit_team_size = settings.FREE_TEAM_SIZE
    elif subscription.plan == SubscriptionPlan.FREE:
        limit_secrets = settings.FREE_SECRETS_PER_MONTH
        limit_attachments = settings.FREE_MAX_ATTACHMENT_SIZE
        limit_team_size = settings.FREE_TEAM_SIZE
    elif subscription.plan == SubscriptionPlan.PRO:
        limit_secrets = settings.PRO_SECRETS_PER_MONTH
        limit_attachments = settings.PRO_MAX_ATTACHMENT_SIZE
        limit_team_size = settings.PRO_TEAM_SIZE
    elif subscription.plan == SubscriptionPlan.TEAM:
        limit_secrets = settings.TEAM_SECRETS_PER_MONTH
        limit_attachments = settings.TEAM_MAX_ATTACHMENT_SIZE
        limit_team_size = settings.TEAM_TEAM_SIZE
    else:
        limit_secrets = 9999999
        limit_attachments = 100 * 1024 * 1024
        limit_team_size = 9999

    return {
        "secrets_created_this_month": usage.secrets_created_this_month if usage else 0,
        "secret_requests_this_month": usage.secret_requests_this_month if usage else 0,
        "attachment_bytes_this_month": usage.attachment_bytes_this_month if usage else 0,
        "limit_secrets": limit_secrets,
        "limit_attachments": limit_attachments,
        "limit_team_size": limit_team_size
    }


@router.post("/checkout")
def create_checkout_session(
    data: CreateCheckoutSession,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    try:
        # Create or get Stripe customer
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": current_user.id}
            )
            customer_id = customer.id

            if subscription:
                subscription.stripe_customer_id = customer_id
                db.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": data.price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={"user_id": current_user.id}
        )

        return {"checkout_url": checkout_session.url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/portal")
def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=f"{settings.CORS_ORIGINS[0]}/dashboard"
        )

        return {"portal_url": portal_session.url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/sync")
def sync_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually sync subscription from Stripe (useful for local dev)"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription found"
        )

    try:
        # Get all subscriptions for this customer
        stripe_subs = stripe.Subscription.list(customer=subscription.stripe_customer_id)

        if stripe_subs.data:
            # Get the first active subscription
            stripe_sub = stripe_subs.data[0]
            price_id = stripe_sub["items"]["data"][0]["price"]["id"]

            # Update plan based on price ID
            if price_id == settings.STRIPE_PRICE_ID_PRO:
                subscription.plan = SubscriptionPlan.PRO
            elif price_id == settings.STRIPE_PRICE_ID_TEAM:
                subscription.plan = SubscriptionPlan.TEAM
            else:
                subscription.plan = SubscriptionPlan.FREE

            subscription.stripe_subscription_id = stripe_sub.id
            subscription.status = SubscriptionStatus.ACTIVE if stripe_sub.status == "active" else SubscriptionStatus.CANCELED
            db.commit()

        return subscription

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync subscription: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]

        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if subscription:
            subscription.stripe_subscription_id = session["subscription"]
            subscription.status = SubscriptionStatus.ACTIVE

            # Get the subscription details to determine the plan
            stripe_sub = stripe.Subscription.retrieve(session["subscription"])
            price_id = stripe_sub["items"]["data"][0]["price"]["id"]

            # Update plan based on price ID
            if price_id == settings.STRIPE_PRICE_ID_PRO:
                subscription.plan = SubscriptionPlan.PRO
            elif price_id == settings.STRIPE_PRICE_ID_TEAM:
                subscription.plan = SubscriptionPlan.TEAM

            db.commit()

    elif event["type"] == "customer.subscription.updated":
        stripe_sub = event["data"]["object"]

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub["id"]
        ).first()

        if subscription:
            # Update plan based on price ID
            if stripe_sub["items"]["data"][0]["price"]["id"] == settings.STRIPE_PRICE_ID_PRO:
                subscription.plan = SubscriptionPlan.PRO
            elif stripe_sub["items"]["data"][0]["price"]["id"] == settings.STRIPE_PRICE_ID_TEAM:
                subscription.plan = SubscriptionPlan.TEAM

            subscription.status = SubscriptionStatus.ACTIVE
            db.commit()

    elif event["type"] == "customer.subscription.deleted":
        stripe_sub = event["data"]["object"]

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub["id"]
        ).first()

        if subscription:
            subscription.plan = SubscriptionPlan.FREE
            subscription.status = SubscriptionStatus.CANCELED
            db.commit()

    return {"status": "success"}
