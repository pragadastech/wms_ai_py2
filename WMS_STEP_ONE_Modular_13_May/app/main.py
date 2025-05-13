from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.user import router as user_router
from app.routes.netsuite import router as netsuite_router
from app.routes.bin_management import router as bin_management_router
from app.middleware.exception_handler import GlobalExceptionMiddleware

app = FastAPI(
    title="Warehouse Management System API",
    description="""
    # WMS API Documentation
    
    This API provides integration with NetSuite for warehouse management operations.
    
    ## Features
    
    * **User Authentication** - Secure JWT-based authentication
    * **Data Synchronization** - Fetch and store data from NetSuite
    * **Inventory Management** - Manage warehouse inventory
    * **Bin Management** - Track item locations in the warehouse
    
    ## Authentication
    
    All API endpoints are protected and require a valid JWT token.
    To authenticate, use the `/token` endpoint with valid credentials.
    
    ```
    POST /token
    {
        "username": "your_username",
        "password": "your_password"
    }
    ```
    
    Include the token in the Authorization header of subsequent requests:
    
    ```
    Authorization: Bearer your_token_here
    ```
    
    ## Test Credentials
    
    For development and testing purposes, you can use these credentials:
    
    ### Admin User
    ```json
    {
      "username": "admin",
      "password": "admin123"
    }
    ```
    
    ### Regular User
    ```json
    {
      "userid": "user_123",
      "password": "User12345678"
    }
    ```
    
    > **⚠️ Important**: These are test credentials and should be changed in production environments.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Operations related to user authentication"
        },
        {
            "name": "Admin",
            "description": "Administrative operations"
        },
        {
            "name": "Data",
            "description": "Data retrieval endpoints for the application"
        },
        {
            "name": "NetSuite",
            "description": "NetSuite API integration endpoints"
        },
        {
            "name": "Bin Management",
            "description": "Operations related to bin management"
        }
    ]
)

# app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
# Add global exception handler middleware
app.add_middleware(GlobalExceptionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://pragva.in", "https://pragva.in"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(user_router, tags=["Data"])
app.include_router(netsuite_router, tags=["NetSuite"])
app.include_router(bin_management_router, tags=["Bin Management"])