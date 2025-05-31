from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from models import AccountType

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserRegistrationRequest(UserBase):
    """Schema for user registration request"""
    password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, confirm_password, values):
        if 'password' in values and confirm_password != values['password']:
            raise ValueError('Passwords do not match')
        return confirm_password
    
    @validator('password')
    def validate_password_strength(cls, password):
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        return password

class UserLoginRequest(BaseModel):
    """Schema for user login request"""
    username_or_email: str
    password: str

class AccountTypeSelectionRequest(BaseModel):
    """Schema for account type selection after first login"""
    account_type: AccountType

class UserProfileUpdateRequest(BaseModel):
    """Schema for updating user profile information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user response data"""
    id: int
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    account_type: Optional[AccountType] = None
    is_active: bool
    is_verified: bool
    has_completed_account_selection: bool
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str
    user: UserResponse

class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, confirm_password, values):
        if 'new_password' in values and confirm_password != values['new_password']:
            raise ValueError('Passwords do not match')
        return confirm_password 