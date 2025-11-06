from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import User, UserCreate, UserUpdate
from app.services.auth import get_current_user, verify_clerk_token
from app.services.user import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=User,
    summary="Get Current User",
    description="Retrieves the complete profile for the currently authenticated user.",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    An endpoint to fetch the details of the user who is currently authenticated.
    The user is identified by the JWT token in the Authorization header.
    """
    return current_user


@router.put(
    "/me",
    response_model=User,
    summary="Update Current User",
    description="Updates the profile for the currently authenticated user.",
)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Allows the authenticated user to update their own profile information,
    such as first name and last name.
    """
    user_service = UserService(db)
    return user_service.update_user(current_user.id, user_update)


@router.post(
    "/verify",
    summary="Verify Token and Get User",
    description="Verifies a JWT token from the auth provider (Clerk), then finds or creates a user in the local database. This endpoint is typically called after a successful login on the frontend.",
)
async def verify_token(token: str, db: Session = Depends(get_db)):
    """
    Verifies a token and returns the corresponding user profile.

    - **token**: The JWT token provided by the frontend after authentication.
    """
    try:
        user_data = verify_clerk_token(token)
        user_service = UserService(db)
        user = user_service.get_or_create_user(user_data)
        return {"user": user}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}"
        )
