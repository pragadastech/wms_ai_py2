from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.models.response import DataResponse
from app.models.bin_count import BinCountRequest
from app.database.bin_operations import store_bin_counts

router = APIRouter()

@router.post("/bin-count", response_model=DataResponse)
async def process_bin_count(
    data: BinCountRequest,
    current_user: tuple = Depends(get_current_user)
):
    """
    Process bin count data and store in database
    
    The data is structured as follows:
    {
        "action": "binCount",
        "location": 10,
        "binId": 1234,
        "itemData": [
            {
                "itemId": 3542,
                "quantity": 2
            },
            ...
        ]
    }
    """
    # Transform the data to match the expected format for storage
    bin_data = {
        str(data.binId): [
            {
                "itemId": item.itemId,
                "locationId": data.location,
                "quantity": item.quantity
            }
            for item in data.itemData
        ]
    }
    
    # Log the bin count to console
    bin_count = len(bin_data)
    total_items = sum(len(items) for items in bin_data.values())
    print(f"Received bin count: {bin_count} bins with {total_items} items")
    
    # Store the data in the database
    result = await store_bin_counts(bin_data)
    
    # Return a response
    return DataResponse(
        message=result["message"],
        total_records=result["total_records"],
        data={
            "bins_processed": bin_count,
            "items_processed": total_items,
            "operation_details": result
        }
    ) 