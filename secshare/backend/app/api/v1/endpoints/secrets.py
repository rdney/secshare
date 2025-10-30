from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import secrets as secrets_module
import base64
from typing import List
from app.db.base import get_db
from app.schemas.secret import SecretCreate, SecretResponse, SecretView
from app.models.secret import Secret
from app.models.access_log import AccessLog
from app.models.user import User
from app.models.usage_stats import UsageStats
from app.core.security import SecretEncryption
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()


def check_usage_limits(db: Session, user: User):
    """Check if user has exceeded their monthly secret limit"""
    usage = db.query(UsageStats).filter(UsageStats.user_id == user.id).first()

    if not usage:
        return True

    # Get subscription limits
    subscription = user.subscription
    is_free_plan = not subscription or subscription.plan.value == "FREE"

    if not subscription:
        limit = settings.FREE_SECRETS_PER_MONTH
    elif subscription.plan.value == "FREE":
        limit = settings.FREE_SECRETS_PER_MONTH
    elif subscription.plan.value == "PRO":
        limit = settings.PRO_SECRETS_PER_MONTH
    elif subscription.plan.value == "TEAM":
        limit = settings.TEAM_SECRETS_PER_MONTH
    else:
        limit = 9999999  # Enterprise

    # Reset usage on 1st of month (only for free plan)
    if is_free_plan:
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

    if usage.secrets_created_this_month >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Monthly secret limit reached ({limit}). Upgrade your plan."
        )

    return True


@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
def create_secret(
    secret_in: SecretCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check usage limits
    check_usage_limits(db, current_user)

    # Generate encryption key and IV
    key = SecretEncryption.generate_key()
    iv = SecretEncryption.generate_iv()

    # Encrypt the secret content
    encrypted_content = SecretEncryption.encrypt(secret_in.content, key, iv)

    # Encrypt the key itself with master key
    encrypted_key = SecretEncryption.encrypt_key(key, settings.SECRET_KEY)

    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(hours=secret_in.expires_in_hours)

    # Create secret
    secret = Secret(
        id=secrets_module.token_urlsafe(16),
        encrypted_content=base64.b64encode(encrypted_content).decode(),
        encrypted_key=base64.b64encode(encrypted_key).decode(),
        iv=base64.b64encode(iv).decode(),
        max_views=secret_in.max_views,
        expires_at=expires_at,
        created_by_id=current_user.id,
        team_id=current_user.team_id
    )

    db.add(secret)

    # Update usage stats
    usage = db.query(UsageStats).filter(UsageStats.user_id == current_user.id).first()
    if usage:
        usage.secrets_created_this_month += 1

    db.commit()
    db.refresh(secret)

    return secret


@router.get("/{secret_id}", response_model=SecretView)
def get_secret(
    secret_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    secret = db.query(Secret).filter(Secret.id == secret_id).first()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    # Check if expired
    if secret.expires_at < datetime.now(timezone.utc):
        db.delete(secret)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Secret has expired"
        )

    # Check if max views reached
    if secret.current_views >= secret.max_views:
        db.delete(secret)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Secret has been viewed maximum times"
        )

    # Decrypt the secret
    try:
        encrypted_key = base64.b64decode(secret.encrypted_key)
        key = SecretEncryption.decrypt_key(encrypted_key, settings.SECRET_KEY)

        iv = base64.b64decode(secret.iv)
        encrypted_content = base64.b64decode(secret.encrypted_content)

        decrypted_content = SecretEncryption.decrypt(encrypted_content, key, iv)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt secret"
        )

    # Increment view count
    secret.current_views += 1

    # Log access
    access_log = AccessLog(
        id=secrets_module.token_urlsafe(16),
        secret_id=secret.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(access_log)

    # Update usage stats for creator
    usage = db.query(UsageStats).filter(UsageStats.user_id == secret.created_by_id).first()
    if usage:
        usage.secret_requests_this_month += 1

    db.commit()

    return {
        "id": secret.id,
        "content": decrypted_content,
        "current_views": secret.current_views,
        "max_views": secret.max_views,
        "expires_at": secret.expires_at,
        "has_attachment": secret.has_attachment,
        "attachment_url": secret.attachment_url,
        "attachment_name": secret.attachment_name
    }


@router.get("", response_model=List[SecretResponse])
def list_secrets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    secrets = db.query(Secret).filter(
        Secret.created_by_id == current_user.id,
        Secret.expires_at > datetime.now(timezone.utc)
    ).order_by(Secret.created_at.desc()).all()

    return secrets


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_secret(
    secret_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    secret = db.query(Secret).filter(
        Secret.id == secret_id,
        Secret.created_by_id == current_user.id
    ).first()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    db.delete(secret)
    db.commit()

    return None


@router.get("/{secret_id}/logs", response_model=List[dict])
def get_secret_logs(
    secret_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    secret = db.query(Secret).filter(
        Secret.id == secret_id,
        Secret.created_by_id == current_user.id
    ).first()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )

    logs = db.query(AccessLog).filter(
        AccessLog.secret_id == secret_id
    ).order_by(AccessLog.accessed_at.desc()).all()

    return [
        {
            "id": log.id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "accessed_at": log.accessed_at
        }
        for log in logs
    ]
