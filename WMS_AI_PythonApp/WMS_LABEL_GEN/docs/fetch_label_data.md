# Fetch Label Data

## Overview
A FastAPI-based service for retrieving and managing shipping label data. This module provides REST API endpoints for accessing label information stored in Supabase.

## Features
- REST API endpoints for label retrieval
- Supabase database integration
- Pydantic models for data validation
- Support for filtering by order ID and item ID
- Logging and error handling

## Running the Program

### Prerequisites
1. Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Running the API Server
1. Activate the virtual environment:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. Start the FastAPI server:
```bash
uvicorn fetch_label_data:app --reload
```

The server will start at `http://localhost:8000`

### Testing the API
1. Open your browser and visit:
   - API documentation: `http://localhost:8000/docs`
   - Alternative documentation: `http://localhost:8000/redoc`

2. Test endpoints using curl:
```bash
# Get all labels for an order
curl http://localhost:8000/labels/ORDER123

# Get labels for a specific item
curl http://localhost:8000/labels/ORDER123?item_id=ITEM456
```

### Expected Behavior
- Server starts on port 8000
- API documentation is available at /docs
- Endpoints return JSON responses
- Error responses include detailed messages

### Common Issues and Solutions
1. **Port Already in Use**
   - Solution: Change port using `--port` flag:
   ```bash
   uvicorn fetch_label_data:app --reload --port 8001
   ```

2. **Supabase Connection Error**
   - Solution: Verify `.env` file contains correct credentials

3. **Module Not Found Error**
   - Solution: Ensure you're in the correct directory and virtual environment is activated

## API Endpoints

### GET `/labels/{order_id}`
Retrieves all labels for a specific order.

#### Parameters
- `order_id` (path parameter): The ID of the order to fetch labels for
- `item_id` (query parameter, optional): Specific item ID to filter labels

#### Response
Returns a JSON object with the following structure:
```json
{
    "order_id": {
        "item_id": {
            "ship_label_data": [
                {
                    "label_id": 1,
                    "label_data": "HTML content",
                    "packingslip_data": "Packing slip content",
                    "tracking_number": "TRACK123",
                    "sscc_code": "SSCC123456789"
                }
            ]
        }
    }
}
```

#### Error Responses
- 404: No labels found for the specified order/item
- 500: Internal server error

## Data Models

### `ShipLabelItem`
Model for individual label data:
```python
class ShipLabelItem(BaseModel):
    label_id: int
    label_data: str
    packingslip_data: Optional[str] = ""
    tracking_number: Optional[str] = ""
    sscc_code: str
```

### `LabelData`
Model for grouped label data:
```python
class LabelData(BaseModel):
    ship_label_data: List[ShipLabelItem] = Field(default_factory=list)
```

## Functions

### `get_supabase_client()`
Initializes and returns a Supabase client.
- **Returns**: Supabase Client instance
- **Raises**: ValueError if credentials are missing

### `get_labels(order_id, item_id=None)`
API endpoint for retrieving labels.
- **Parameters**:
  - `order_id`: Order identifier
  - `item_id`: Optional item identifier
- **Returns**: Validated label data
- **Raises**: HTTPException for errors

## Usage Example
```python
# Using the API with requests
import requests

# Get all labels for an order
response = requests.get("http://localhost:8000/labels/ORDER123")
labels = response.json()

# Get labels for a specific item
response = requests.get("http://localhost:8000/labels/ORDER123?item_id=ITEM456")
item_labels = response.json()
```

## Dependencies
- fastapi
- python-dotenv
- supabase
- pydantic
- logging (standard library)

## Error Handling
- Validates input parameters
- Handles database connection errors
- Manages missing data scenarios
- Provides detailed error messages

## Notes
- Requires valid Supabase credentials in .env file
- Implements duplicate prevention for label data
- Uses Pydantic for response validation
- Includes comprehensive logging 