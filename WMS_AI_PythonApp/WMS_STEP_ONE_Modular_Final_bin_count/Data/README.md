# WMS AI Python Application Documentation

<div align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Supabase-181818?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase">
  <img src="https://img.shields.io/badge/NetSuite-FF6B6B?style=for-the-badge&logo=netsuite&logoColor=white" alt="NetSuite">
</div>

## 🚀 Introduction

Welcome to the WMS AI Python Application! This is a modern, fast, and secure web application built with FastAPI that helps manage warehouse operations and integrates with NetSuite. The application provides a robust API for warehouse management, inventory tracking, and seamless integration with NetSuite's business management system.

### Key Benefits
- ⚡ High-performance API built with FastAPI
- 🔒 Enterprise-grade security with JWT authentication
- 📊 Real-time data synchronization with NetSuite
- 🗄️ Scalable database architecture with Supabase
- 📱 RESTful API design for easy integration

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [API Endpoints](#-api-endpoints)
- [Authentication](#-authentication)
- [Error Handling](#-error-handling)
- [Logging](#-logging)
- [Development](#-development)

## ✨ Features

### Core Features
- 🔐 Secure authentication with JWT tokens
- 📊 NetSuite integration for:
  - Locations
  - Bins
  - Users
  - Inventory
  - Items
  - Sales Orders
- 🗄️ Supabase database integration
- 📝 Comprehensive logging
- 🔄 Token refresh mechanism
- ⏱️ Session management

### Advanced Features
- 🔄 Real-time data synchronization
- 📈 Performance monitoring
- 🔒 Role-based access control
- 📱 Mobile-friendly API design
- 🛡️ Rate limiting and security measures
- 📊 Data validation and sanitization

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

### System Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Git version control system
- Virtual environment support

### Service Accounts
- A Supabase account with database access
- NetSuite API credentials with appropriate permissions
- Environment for storing sensitive credentials

## 💻 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd WMS_AI_PythonApp
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# NetSuite Configuration
NETSUITE_BASE_URL=https://4809897-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl
NETSUITE_CONSUMER_KEY=your_netsuite_consumer_key
NETSUITE_CONSUMER_SECRET=your_netsuite_consumer_secret
NETSUITE_TOKEN_ID=your_netsuite_token_id
NETSUITE_TOKEN_SECRET=your_netsuite_token_secret
NETSUITE_ACCOUNT_ID=your_netsuite_account_id

# Application Settings
TOKEN_REFRESH_THRESHOLD=5
TOKEN_ACTIVITY_WINDOW=30
```

## 🏃 Running the Application

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points
- API Documentation: `http://localhost:8000/docs`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔌 API Endpoints

### Authentication Endpoints

#### 1. Admin Login
**Endpoint:** `POST /token`

**Request:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 2. User Login
**Endpoint:** `POST /user/login`

**Request:**
```json
{
  "userid": "user123",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Refresh Token
**Endpoint:** `POST /refresh-token`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Admin Endpoints

#### 1. Admin Dashboard
**Endpoint:** `GET /admin/dashboard`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "message": "Welcome Admin!",
  "total_users": 150,
  "users": [
    {
      "userid": "user123",
      "email": "user@example.com",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### 2. Register User
**Endpoint:** `POST /admin/register-user`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Request:**
```json
{
  "userid": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "userid": "newuser",
  "email": "newuser@example.com"
}
```

### Data Endpoints

#### 1. Get Locations
**Endpoint:** `GET /data_locations`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": 200,
  "message": "Data retrieved successfully",
  "total_records": 50,
  "data": {
    "location_1": {
      "name": "Main Warehouse",
      "address": "123 Main St",
      "capacity": 1000
    }
  }
}
```

#### 2. Get Bins
**Endpoint:** `GET /data_bins`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": 200,
  "message": "Data retrieved successfully",
  "total_records": 100,
  "data": {
    "bin_1": {
      "location": "Main Warehouse",
      "capacity": 100,
      "current_quantity": 50
    }
  }
}
```

### NetSuite Integration Endpoints

#### 1. Fetch NetSuite Locations
**Endpoint:** `GET /netsuite/locations`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 200,
  "total_pages": 2,
  "data": {
    "location_1": {
      "internal_id": "123",
      "name": "NetSuite Location 1",
      "address": "456 Business Ave"
    }
  }
}
```

#### 2. Fetch NetSuite Inventory
**Endpoint:** `GET /netsuite/inventory`

**Headers:**
```
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 500,
  "total_pages": 5,
  "data": {
    "item_1": {
      "internal_id": "789",
      "name": "Product A",
      "quantity": 100,
      "location": "Main Warehouse"
    }
  }
}
```

## 🔐 Authentication

### JWT Authentication Flow

1. **Login**
   ```bash
   curl -X POST "http://localhost:8000/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin&password=password"
   ```

2. **Using the Token**
   ```bash
   curl -X GET "http://localhost:8000/admin/dashboard" \
        -H "Authorization: Bearer <your_token>"
   ```

### Token Management
- Tokens expire after 30 minutes of inactivity
- Refresh tokens using `/refresh-token` endpoint
- Session timeout after 30 minutes of inactivity

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Verify authentication token |
| 403 | Forbidden | Check user permissions |
| 404 | Not Found | Verify resource existence |
| 500 | Internal Error | Contact support |

### Error Response Format
```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "validation_error"
}
```

## 📝 Logging

### Log Configuration
- Log level: INFO
- Output: Console and file
- File: `api_operations.log`
- Format: JSON

### Log Fields
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "operation": "user_login",
  "user_id": "user123",
  "status": "success",
  "duration_ms": 150
}
```

## 🛠️ Development

### Project Structure
```
WMS_AI_PythonApp/
├── main.py              # Main application file
├── requirements.txt     # Dependencies
├── .env                # Environment variables
├── api_operations.log  # Application logs
└── README.md          # Documentation
```

### Development Guidelines
1. Follow PEP 8 style guide
2. Write unit tests for new features
3. Document all API endpoints
4. Use type hints
5. Implement error handling
6. Follow security best practices

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=main
``` 