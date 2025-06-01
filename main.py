from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from config import settings
from database import engine, Base
from api.auth import auth_router
from api.users import users_router
from api.images import router as images_router
from models import User, Image, ProcessedImage, DemoImage  # Import to ensure tables are created

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Creates database tables on startup and ensures storage directories exist.
    """
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    
    # Ensure storage directories exist
    import os
    storage_dirs = [
        "storage/images",
        "storage/thumbnails",
        "storage/processed",
        "storage/demo",
        "storage/demo/thumbnails"
    ]
    
    for directory in storage_dirs:
        os.makedirs(directory, exist_ok=True)
    print("Storage directories created successfully")
    
    yield
    # Cleanup code can be added here if needed

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

def custom_openapi():
    """Custom OpenAPI schema with JWT Bearer authentication"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )
    
    # Add OAuth2 Password flow for Swagger UI login
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/token",
                    "scopes": {}
                }
            },
            "description": "OAuth2 Password flow for Swagger UI authentication. \n\n"
                          "**How to authenticate:**\n"
                          "1. Click the 'Authorize' button above\n"
                          "2. Enter your username/email and password\n"
                          "3. Click 'Authorize'\n"
                          "4. Swagger will automatically add authentication headers to all protected endpoints!\n\n"
                          "**Test Credentials:**\n"
                          "- Username: `testuser` or `test@example.com`\n"
                          "- Password: `TestPassword123`"
        }
    }
    
    # Apply security to all protected endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            # Skip login and register endpoints (they don't need auth)
            if path in ["/auth/login", "/auth/register", "/", "/health"] or method == "options":
                continue
            
            # Add security requirement to protected endpoints
            if "security" not in openapi_schema["paths"][path][method]:
                openapi_schema["paths"][path][method]["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(images_router)

@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Paint Color Swap API",
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

@app.get("/swagger-auth-help")
async def swagger_auth_help():
    """
    Instructions for authenticating in Swagger UI to test protected endpoints.
    
    This endpoint provides step-by-step instructions for getting a JWT token
    and using it in Swagger UI to test protected endpoints.
    """
    return {
        "title": "🔐 Swagger UI Authentication Guide",
        "description": "Follow these steps to test protected endpoints in Swagger UI",
        "steps": [
            {
                "step": 1,
                "title": "Create a test user (if needed)",
                "description": "Use the /auth/register endpoint or run the create_test_user.py script",
                "example_credentials": {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "TestPassword123"
                }
            },
            {
                "step": 2,
                "title": "Login to get JWT token",
                "description": "Use the /auth/login endpoint with your credentials",
                "endpoint": "/auth/login",
                "example_request": {
                    "username_or_email": "testuser",
                    "password": "TestPassword123"
                }
            },
            {
                "step": 3,
                "title": "Copy the access_token from login response",
                "description": "Copy the 'access_token' value from the JSON response"
            },
            {
                "step": 4,
                "title": "Authorize in Swagger UI",
                "description": "Click the 'Authorize' button at the top of the Swagger UI page"
            },
            {
                "step": 5,
                "title": "Enter your token",
                "description": "Paste your JWT token (without 'Bearer' prefix) and click 'Authorize'"
            },
            {
                "step": 6,
                "title": "Test protected endpoints",
                "description": "Now you can test any endpoint that requires authentication!"
            }
        ],
        "quick_test_script": {
            "description": "Run this script to create a test user and get a token",
            "command": "python create_test_user.py",
            "location": "Backend/create_test_user.py"
        },
        "protected_endpoints_examples": [
            "/users/me",
            "/users/me (PUT)",
            "/auth/account-type",
            "/auth/refresh-token"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
