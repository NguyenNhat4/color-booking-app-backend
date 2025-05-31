from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from config import settings
from database import engine, Base
from api.auth import auth_router
from api.users import users_router
from models import User  # Import to ensure tables are created

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Creates database tables on startup.
    """
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
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
    
    # Add JWT Bearer authentication scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: your_token_here"
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
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
