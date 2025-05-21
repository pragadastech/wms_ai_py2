from fastapi import APIRouter, Depends, Body, HTTPException
from app.auth.dependencies import get_current_user
from app.models.response import DataResponse
from app.models.bin_count import BinCountRequest
from typing import Dict, List, Any
from app.database.bin_operations import store_bin_counts
from app.database.supabase import supabase

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
      "location": 9,
      "binId": 3797,
      "binName": "My Bin",
      "locationName": "Main Warehouse",
      "userName": "John doe",
      "itemData": [
        {
          "itemId": 71190,
          "itemName": "Example Item",
          "quantity": 2
        },
        {
          "itemId": 62063,
          "itemName": "Example Item",
          "quantity": 1
        }
      ]
    }
    """
    # Validate input data
    if data.action != "binCount":
        raise HTTPException(status_code=400, detail="Invalid action field")
    
    # Extract data
    bin_id = str(data.binId)
    location_id = data.location
    item_data = data.itemData
    
    # Transform to the format expected by store_bin_counts
    transformed_data = {
        "bins": {
            bin_id: [
                {
                    "itemId": item.itemId,
                    "itemName": item.itemName,
                    "locationId": location_id,
                    "quantity": item.quantity
                } for item in item_data
            ]
        }
    }
    
    # Add metadata to the transformed data
    transformed_data["metadata"] = {
        "binName": data.binName,
        "locationName": data.locationName,
        "userName": data.userName
    }
    
    # Log the bin count to console
    item_count = len(item_data)
    print(f"Received bin count: Bin {bin_id} ({data.binName}) at location {location_id} ({data.locationName}) with {item_count} items by user {data.userName}")
    
    # Store the data in the database
    result = await store_bin_counts(transformed_data["bins"], transformed_data["metadata"])
    
    # Return a response
    return DataResponse(
        message=result["message"],
        total_records=result["total_records"],
        data={
            "bins_processed": 1,
            "items_processed": item_count,
            "operation_details": result,
            "metadata": transformed_data["metadata"]
        }
    )

@router.get("/bin-count-records", response_model=DataResponse)
async def get_bin_count_data(current_user: tuple = Depends(get_current_user)):
    """
    Fetch all bin count records from the bin_count_records table.
    """
    try:
        response = supabase.table("bin_count_records").select("*").execute()
        records = response.data if response.data else []
        return DataResponse(
            message="Bin count records fetched successfully",
            total_records=len(records),
            data=records
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bin count records: {str(e)}") 