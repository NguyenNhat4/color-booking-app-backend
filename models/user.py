from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base

import enum
from datetime import datetime

class AccountType(enum.Enum):
    """Enumeration for different user account types"""
    REGULAR_CUSTOMER = "regular_customer"
    CONTRACTOR = "contractor"
    HOMEOWNER = "homeowner"
    COMPANY = "company"

class User(Base):
    """
    User model for authentication and profile management.
    Supports multiple account types with role-based access.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Personal Information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    # Account Management
    account_type = Column(SQLEnum(AccountType), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    has_completed_account_selection = Column(Boolean, default=False, nullable=False)
    
    # Address Information
    street_address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, default="Vietnam")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, account_type={self.account_type})>"
    
    @property
    def full_name(self):
        """Returns the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def is_business_account(self):
        """Check if user has a business account type"""
        return self.account_type in [AccountType.CONTRACTOR, AccountType.COMPANY] 