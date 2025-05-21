# WMS AI API Documentation

## Base URL
```
http://pragva.in:8000/
```

## Authentication
All API endpoints require JWT authentication unless specified otherwise. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### Authentication

#### 1. Admin Login
```http
POST /token
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=admin&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
```json
{
  "detail": "Incorrect username or password",
  "status_code": 401
}
```

#### 2. User Login
```http
POST /user/login
Content-Type: application/json
```

**Request Body:**
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

**Error Responses:**
```json
{
  "detail": "Incorrect userid or password",
  "status_code": 401
}
```

#### 3. Refresh Token
```http
POST /refresh-token
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
```json
{
  "detail": "Invalid token or expired",
  "status_code": 401
}
```

### Admin Operations

#### 1. Get Admin Dashboard
```http
GET /admin/dashboard
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
  ],
  "new_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
```json
{
  "detail": "Not authorized",
  "status_code": 403
}
```

### Data Operations

#### 1. Get Locations
```http
GET /data_locations
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
      "location_id": "123",
      "location_data": {
        "name": "Main Warehouse",
        "address": "123 Main St"
      }
    }
  },
  "progress": {
    "fetched": 50,
    "total": 100,
    "percentage": 50.0,
    "current_batch": 50,
    "batch_size": 1000
  }
}
```

**Error Responses:**
```json
{
  "detail": "No locations data found",
  "status_code": 404
}
```

#### 2. Get Bins
```http
GET /data_bins
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
      "internal_id": "456",
      "bin_data": {
        "location": "Main Warehouse",
        "capacity": 100
      }
    }
  },
  "progress": {
    "fetched": 100,
    "total": 100,
    "percentage": 100.0,
    "current_batch": 100,
    "batch_size": 1000
  }
}
```

**Error Responses:**
```json
{
  "detail": "No bins data found",
  "status_code": 404
}
```

#### 3. Get Users
```http
GET /data_users
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": 200,
  "message": "Data retrieved successfully",
  "total_records": 50,
  "data": {
    "user_1": {
      "internal_id": "789",
      "user_data": {
        "name": "John Doe",
        "email": "john@example.com"
      }
    }
  },
  "progress": {
    "fetched": 50,
    "total": 50,
    "percentage": 100.0,
    "current_batch": 50,
    "batch_size": 1000
  }
}
```

**Error Responses:**
```json
{
  "detail": "No users data found",
  "status_code": 404
}
```

#### 4. Get Inventory
```http
GET /data_inventory
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": 200,
  "message": "Data retrieved successfully",
  "total_records": 200,
  "data": {
    "item_1": {
      "internal_id": "101",
      "inventory_data": {
        "name": "Product A",
        "quantity": 100,
        "location": "Main Warehouse"
      }
    }
  },
  "progress": {
    "fetched": 200,
    "total": 200,
    "percentage": 100.0,
    "current_batch": 200,
    "batch_size": 1000
  }
}
```

**Error Responses:**
```json
{
  "detail": "No inventory data found",
  "status_code": 404
}
```

#### 5. Get Items
```http
GET /data_items
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": 200,
  "message": "Data retrieved successfully",
  "total_records": 300,
  "data": {
    "item_1": {
      "internal_id": "202",
      "item_data": {
        "name": "Product B",
        "description": "Description of Product B",
        "price": 99.99
      }
    }
  },
  "progress": {
    "fetched": 300,
    "total": 300,
    "percentage": 100.0,
    "current_batch": 300,
    "batch_size": 1000
  }
}
```

**Error Responses:**
```json
{
  "detail": "No items data found",
  "status_code": 404
}
```

#### 6. Get Sales Orders
```http
GET /data_sales_orders
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": 200,
  "message": "Data retrieved successfully",
  "total_records": 150,
  "data": {
    "order_1": {
      "internal_id": "303",
      "sales_order_data": {
        "order_number": "SO-001",
        "customer": "Customer A",
        "total_amount": 999.99
      }
    }
  },
  "progress": {
    "fetched": 150,
    "total": 150,
    "percentage": 100.0,
    "current_batch": 150,
    "batch_size": 1000
  }
}
```

**Error Responses:**
```json
{
  "detail": "No sales orders data found",
  "status_code": 404
}
```

### NetSuite Integration

#### 1. Fetch NetSuite Locations
```http
GET /netsuite/locations
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 200,
  "total_pages": 2,
  "successful_operations": 200,
  "fetching_time": 5.2,
  "storage_time": 1.8,
  "total_processing_time": 7.0,
  "data": {
    "location_1": {
      "internal_id": "123",
      "name": "NetSuite Location 1",
      "address": "456 Business Ave"
    }
  }
}
```

**Error Responses:**
```json
{
  "detail": "NetSuite API error",
  "status_code": 500
}
```

#### 2. Fetch NetSuite Users
```http
GET /netsuite/users
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 100,
  "total_pages": 1,
  "successful_operations": 100,
  "fetching_time": 3.5,
  "storage_time": 1.2,
  "total_processing_time": 4.7,
  "data": {
    "user_1": {
      "internal_id": "456",
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

**Error Responses:**
```json
{
  "detail": "NetSuite API error",
  "status_code": 500
}
```

#### 3. Fetch NetSuite Bins
```http
GET /netsuite/bins
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 300,
  "total_pages": 3,
  "successful_operations": 300,
  "fetching_time": 8.1,
  "storage_time": 2.3,
  "total_processing_time": 10.4,
  "data": {
    "bin_1": {
      "internal_id": "789",
      "location": "Main Warehouse",
      "capacity": 100
    }
  }
}
```

**Error Responses:**
```json
{
  "detail": "NetSuite API error",
  "status_code": 500
}
```

#### 4. Fetch NetSuite Inventory
```http
GET /netsuite/inventory
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 500,
  "total_pages": 5,
  "successful_operations": 500,
  "fetching_time": 12.5,
  "storage_time": 3.8,
  "total_processing_time": 16.3,
  "data": {
    "item_1": {
      "internal_id": "101",
      "name": "Product A",
      "quantity": 100,
      "location": "Main Warehouse"
    }
  }
}
```

**Error Responses:**
```json
{
  "detail": "NetSuite API error",
  "status_code": 500
}
```

#### 5. Fetch NetSuite Items
```http
GET /netsuite/items
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 400,
  "total_pages": 4,
  "successful_operations": 400,
  "fetching_time": 10.2,
  "storage_time": 3.1,
  "total_processing_time": 13.3,
  "data": {
    "item_1": {
      "internal_id": "202",
      "name": "Product B",
      "description": "Description of Product B",
      "price": 99.99
    }
  }
}
```

**Error Responses:**
```json
{
  "detail": "NetSuite API error",
  "status_code": 500
}
```

#### 6. Fetch NetSuite Sales Orders
```http
GET /netsuite/sales-orders
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Data fetched and stored successfully",
  "total_records": 250,
  "total_pages": 3,
  "successful_operations": 250,
  "fetching_time": 9.8,
  "storage_time": 2.9,
  "total_processing_time": 12.7,
  "data": {
    "order_1": {
      "internal_id": "303",
      "order_number": "SO-001",
      "customer": "Customer A",
      "total_amount": 999.99
    }
  }
}
```

**Error Responses:**
```json
{
  "detail": "NetSuite API error",
  "status_code": 500
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters or data |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server-side error |
