import os
from decouple import config
from typing import List

class Settings:
    """Application settings and configuration"""
    
    # Database Configuration
    DATABASE_URL: str = config(
        "DATABASE_URL", 
        default="sqlite:///./paint_color_swap.db"
    )
    
    # Security Configuration
    SECRET_KEY: str = config(
        "SECRET_KEY", 
        default="your-super-secret-key-change-this-in-production"
    )
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", 
        default=30, 
        cast=int
    )
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://localhost:62779",  # Flutter web debug port
        "http://127.0.0.1:62779",  # Alternative localhost format
        "*",  # Allow all origins for development (remove in production)
    ]
    
    # Application Settings
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    PROJECT_NAME: str = "Paint Color Swap API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for Paint Color Swap mobile application"

settings = Settings() 
print(settings.DATABASE_URL)

