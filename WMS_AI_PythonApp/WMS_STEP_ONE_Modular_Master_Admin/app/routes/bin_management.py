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
      "itemData": [
        {
          "itemId": 71190,
          "quantity": 2
        },
        {
          "itemId": 62063,
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
                    "locationId": location_id,
                    "quantity": item.quantity
                } for item in item_data
            ]
        }
    }
    
    # Log the bin count to console
    item_count = len(item_data)
    print(f"Received bin count: Bin {bin_id} at location {location_id} with {item_count} items")
    
    # Store the data in the database
    result = await store_bin_counts(transformed_data["bins"])
    
    # Return a response
    return DataResponse(
        message=result["message"],
        total_records=result["total_records"],
        data={
            "bins_processed": 1,
            "items_processed": item_count,
            "operation_details": result
        }
    )

@router.get("/bin-count-records", response_model=DataResponse)
async def get_all_bin_count_records(
    current_user: tuple = Depends(get_current_user)
):
    """
    Fetch all records from the bin_count_records table
    
    Returns:
        DataResponse containing all bin count records with their details
    """
    try:
        # Fetch all records from bin_count_records table
        response = supabase.table("bin_count_records").select("*").execute()
        
        if not response.data:
            return DataResponse(
                message="No bin count records found",
                total_records=0,
                data={}
            )
        
        # Transform the list of records into a dictionary with bin_id as key
        records_dict = {
            record["bin_id"]: record
            for record in response.data
        }
        
        return DataResponse(
            message="Bin count records retrieved successfully",
            total_records=len(response.data),
            data=records_dict
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bin count records: {str(e)}") 