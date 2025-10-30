from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import secrets
from app.db.base import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.usage_stats import UsageStats
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        id=secrets.token_urlsafe(16),
        email=user_in.email,
        name=user_in.name,
        password_hash=get_password_hash(user_in.password)
    )
    db.add(user)

    # Create free subscription
    subscription = Subscription(
        id=secrets.token_urlsafe(16),
        user_id=user.id,
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.ACTIVE
    )
    db.add(subscription)

    # Create usage stats
    now = datetime.now(timezone.utc)
    usage = UsageStats(
        id=secrets.token_urlsafe(16),
        user_id=user.id,
        period_start=now,
        period_end=now.replace(day=1, month=now.month + 1 if now.month < 12 else 1)
    )
    db.add(usage)

    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
