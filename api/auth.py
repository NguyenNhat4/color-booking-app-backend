from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from database import get_database_session
from services.auth_service import AuthenticationService, UserService
from schemas import (
    UserRegistrationRequest,
    UserLoginRequest,
    AccountTypeSelectionRequest,
    UserProfileUpdateRequest,
    UserResponse,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm
)
from models.user import User
from config import settings

# Create router for authentication endpoints
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for JWT token
security_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    database_session: Session = Depends(get_database_session)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    This function will be used to protect routes that require authentication.
    """
    token = credentials.credentials
    payload = AuthenticationService.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_service = UserService(database_session)
    user = user_service.get_user_by_id(int(user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistrationRequest,
    database_session: Session = Depends(get_database_session)
):
    """
    Register a new user account.
    Returns user information without sensitive data.
    """
    user_service = UserService(database_session)
    
    try:
        new_user = user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name or "",
            last_name=user_data.last_name or "",
            phone_number=user_data.phone_number or ""
        )
        
        return UserResponse.from_orm(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        logging.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account: {str(e)}"
        )

@auth_router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLoginRequest,
    database_session: Session = Depends(get_database_session)
):
    """
    Authenticate user and return JWT access token.
    """
    user_service = UserService(database_session)
    
    try:
        user = user_service.authenticate_user(
            username_or_email=login_data.username_or_email,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthenticationService.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )



@auth_router.put("/account-type", response_model=UserResponse)
async def select_account_type(
    account_type_data: AccountTypeSelectionRequest,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_database_session)
):
    """
    Set user's account type after first login.
    This enables access to type-specific features and pricing.
    """
    user_service = UserService(database_session)
    
    try:
        updated_user = user_service.update_account_type(
            user_id=current_user.id,  # type: ignore[arg-type]
            account_type=account_type_data.account_type
        )
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update account type"
        )



@auth_router.post("/verify-email/{verification_token}")
async def verify_email(
    verification_token: str,
    database_session: Session = Depends(get_database_session)
):
    """
    Verify user's email address using verification token.
    """
    user_service = UserService(database_session)
    
    if user_service.verify_user_email(verification_token):
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

@auth_router.post("/forgot-password")
async def forgot_password(
    reset_request: PasswordResetRequest,
    database_session: Session = Depends(get_database_session)
):
    """
    Initiate password reset process.
    Sends reset token via email (email sending to be implemented).
    """
    user_service = UserService(database_session)
    
    # Initiate password reset
    reset_token = user_service.initiate_password_reset(reset_request.email)
    
    # Always return success message for security
    # (Don't reveal if email exists in system)
    return {
        "message": "If the email exists, a password reset link has been sent",
        # In development, return token for testing
        "reset_token": reset_token if settings.DEBUG else None
    }

@auth_router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    database_session: Session = Depends(get_database_session)
):
    """
    Reset user password using reset token.
    """
    user_service = UserService(database_session)
    
    if user_service.reset_password(reset_data.token, reset_data.new_password):
        return {"message": "Password reset successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

@auth_router.post("/refresh-token", response_model=TokenResponse)
async def refresh_access_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh JWT access token for authenticated user.
    """
    try:
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthenticationService.create_access_token(
            data={"sub": str(current_user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(current_user)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        ) 