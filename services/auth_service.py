from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User, AccountType
from config import settings
import secrets

# Password hashing context
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthenticationService:
    """Service class for handling user authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return password_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return password_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)

class UserService:
    """Service class for user management operations"""
    
    def __init__(self, database_session: Session):
        self.database_session = database_session
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.database_session.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.database_session.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.database_session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """Get user by username or email"""
        return self.database_session.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
    
    def create_user(self, email: str, username: str, password: str, 
                   first_name: str = "", last_name: str = "", 
                   phone_number: str = "") -> User:
        """Create a new user account"""
        
        # Check if user already exists
        if self.get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if self.get_user_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = AuthenticationService.hash_password(password)
        verification_token = AuthenticationService.generate_verification_token()
        
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            verification_token=verification_token,
            is_active=True,  # Explicitly set based on model default
            is_verified=False, # Already explicit
            has_completed_account_selection=False # Explicitly set based on model default
        )
        
        self.database_session.add(new_user)
        self.database_session.commit()
        self.database_session.refresh(new_user)
        
        return new_user
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password"""
        user = self.get_user_by_username_or_email(username_or_email)
        
        if not user:
            return None
        
        if not AuthenticationService.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )
        
        # Update last login time
        user.last_login = datetime.utcnow()
        self.database_session.commit()
        
        return user
    
    def update_account_type(self, user_id: int, account_type: AccountType) -> User:
        """Update user's account type"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.account_type = account_type
        user.has_completed_account_selection = True
        self.database_session.commit()
        self.database_session.refresh(user)
        
        return user
    
    def update_user_profile(self, user_id: int, profile_data: dict) -> User:
        """Update user profile information"""
        user = self.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update only provided fields
        for field, value in profile_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.database_session.commit()
        self.database_session.refresh(user)
        
        return user
    
    def verify_user_email(self, verification_token: str) -> bool:
        """Verify user email using verification token"""
        user = self.database_session.query(User).filter(
            User.verification_token == verification_token
        ).first()
        
        if not user:
            return False
        
        user.is_verified = True
        user.verification_token = None
        self.database_session.commit()
        
        return True
    
    def initiate_password_reset(self, email: str) -> Optional[str]:
        """Initiate password reset process"""
        user = self.get_user_by_email(email)
        
        if not user:
            # Don't reveal if email exists for security
            return None
        
        reset_token = AuthenticationService.generate_verification_token()
        user.verification_token = reset_token
        self.database_session.commit()
        
        return reset_token
    
    def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Reset user password using reset token"""
        user = self.database_session.query(User).filter(
            User.verification_token == reset_token
        ).first()
        
        if not user:
            return False
        
        user.hashed_password = AuthenticationService.hash_password(new_password)
        user.verification_token = None
        self.database_session.commit()
        
        return True 