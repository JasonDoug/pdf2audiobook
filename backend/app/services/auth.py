from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.schemas import User, TokenData
from app.services.user import UserService

security = HTTPBearer()

def verify_clerk_token(token: str) -> dict:
    try:
        # Decode JWT token (Clerk uses RS256, but for simplicity we'll use HS256 here)
        # In production, you should verify with Clerk's public key
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Extract user information
        user_data = {
            "auth_provider_id": payload.get("sub"),
            "email": payload.get("email"),
            "first_name": payload.get("given_name"),
            "last_name": payload.get("family_name")
        }
        
        return user_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        user_data = verify_clerk_token(credentials.credentials)
        user_service = UserService(db)
        user = user_service.get_user_by_auth_id(user_data["auth_provider_id"])
        
        if user is None:
            raise credentials_exception
            
        return user
    except JWTError:
        raise credentials_exception

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
        
    try:
        user_data = verify_clerk_token(credentials.credentials)
        user_service = UserService(db)
        return user_service.get_user_by_auth_id(user_data["auth_provider_id"])
    except JWTError:
        return None