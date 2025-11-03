from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import User, UserCreate, UserUpdate
from app.services.auth import get_current_user, verify_clerk_token
from app.services.user import UserService

router = APIRouter()

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    return user_service.update_user(current_user.id, user_update)

@router.post("/verify")
async def verify_token(token: str, db: Session = Depends(get_db)):
    try:
        user_data = verify_clerk_token(token)
        user_service = UserService(db)
        user = user_service.get_or_create_user(user_data)
        return {"user": user}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )