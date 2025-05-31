from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_database_session
from services.auth_service import UserService
from schemas import (
    UserProfileUpdateRequest,
    UserResponse
)
from models.user import User
from api.auth import get_current_user

# Create router for user endpoints
users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile information.
    This endpoint provides the same functionality as /auth/me but under /users/me
    for frontend compatibility.
    """
    return UserResponse.from_orm(current_user)

@users_router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_database_session)
):
    """
    Update current authenticated user's profile information.
    Only provided fields will be updated.
    """
    user_service = UserService(database_session)
    
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = profile_data.dict(exclude_unset=True, exclude_none=True)
        
        updated_user = user_service.update_user_profile(
            user_id=current_user.id,  # type: ignore[arg-type]
            profile_data=update_data
        )
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@users_router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Alternative endpoint to get user profile.
    Alias for /users/me for additional frontend compatibility.
    """
    return UserResponse.from_orm(current_user)

@users_router.put("/profile", response_model=UserResponse)
async def update_user_profile_alternative(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_database_session)
):
    """
    Alternative endpoint to update user profile.
    Provides the same functionality as /users/me but under /users/profile.
    """
    user_service = UserService(database_session)
    
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = profile_data.dict(exclude_unset=True, exclude_none=True)
        
        updated_user = user_service.update_user_profile(
            user_id=current_user.id,  # type: ignore[arg-type]
            profile_data=update_data
        )
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        ) 