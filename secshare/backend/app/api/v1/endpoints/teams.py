from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
from app.db.base import get_db
from app.models.user import User
from app.models.team import Team
from app.api.deps import get_current_user

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(
    name: str,
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user already owns a team
    existing_team = db.query(Team).filter(Team.owner_id == current_user.id).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already owns a team"
        )

    # Check if slug is taken
    slug_taken = db.query(Team).filter(Team.slug == slug).first()
    if slug_taken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team slug already taken"
        )

    team = Team(
        id=secrets.token_urlsafe(16),
        name=name,
        slug=slug,
        owner_id=current_user.id
    )
    db.add(team)

    # Add user to team
    current_user.team_id = team.id

    db.commit()
    db.refresh(team)

    return team


@router.get("/me")
def get_my_team(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.team_id:
        return None

    team = db.query(Team).filter(Team.id == current_user.team_id).first()
    return team


@router.get("/{team_id}/members", response_model=List[dict])
def get_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check if user is member of this team
    if current_user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this team"
        )

    members = db.query(User).filter(User.team_id == team_id).all()

    return [
        {
            "id": member.id,
            "email": member.email,
            "name": member.name,
            "is_owner": member.id == team.owner_id
        }
        for member in members
    ]
