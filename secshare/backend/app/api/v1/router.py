from fastapi import APIRouter
from app.api.v1.endpoints import auth, secrets, subscriptions, teams

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(secrets.router, prefix="/secrets", tags=["secrets"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
