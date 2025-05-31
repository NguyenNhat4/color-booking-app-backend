from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_database_session
from services.auth_service import UserService
from schemas import UserResponse, UserProfileUpdateRequest
from models.user import User
from api.auth import get_current_user

# Create router for user profile endpoints
users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile information.
    This endpoint provides the user profile data for the authenticated user.
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
    Only provided fields will be updated, others remain unchanged.
    """
    user_service = UserService(database_session)
    
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = profile_data.dict(exclude_unset=True, exclude_none=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
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



@users_router.delete("/me")
async def delete_current_user_account(
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_database_session)
):
    """
    Delete current authenticated user's account.
    This is a soft delete that deactivates the account.
    """
    user_service = UserService(database_session)
    
    try:
        # Deactivate user by updating is_active to False
        user_service.update_user_profile(
            user_id=current_user.id,  # type: ignore[arg-type]
            profile_data={"is_active": False}
        )
        
        return {
            "message": "Account successfully deactivated",
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        ) 