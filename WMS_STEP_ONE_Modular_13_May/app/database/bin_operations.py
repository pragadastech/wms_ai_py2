from supabase import create_client, Client
from fastapi import HTTPException
from app.config.settings import SUPABASE_URL, SUPABASE_KEY
from app.config.logging_config import setup_logging
from typing import Dict, List, Any

logger = setup_logging()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def store_bin_counts(bin_data: Dict[str, List[Dict[str, Any]]], metadata: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Store bin count data in the bin_count_records table
    
    Args:
        bin_data: Dictionary with bin IDs as keys and arrays of items as values
        metadata: Dictionary containing additional metadata (binName, locationName, userName)
        Example input:
        {
            "98789": [
                {"itemId": 71190, "itemName": "Example Item", "quantity": 2, "locationId": 9},
                {"itemId": 62063, "itemName": "Example Item", "quantity": 1, "locationId": 9}
            ]
        }
        metadata = {
            "binName": "My Bin",
            "locationName": "Main Warehouse",
            "userName": "John doe"
        }
        
    Returns:
        Dictionary with operation results
    """
    try:
        # Prepare records for insertion
        records = []
        for bin_id, items in bin_data.items():
            # Get location from first item (assuming all items in a bin have same location)
            location = items[0].get("locationId") if items else None
            
            # Transform the data into the desired format
            transformed_data = {
                "action": "binCount",
                "location": location,
                "binId": int(bin_id),
                "binName": metadata.get("binName") if metadata else None,
                "locationName": metadata.get("locationName") if metadata else None,
                "userName": metadata.get("userName") if metadata else None,
                "itemData": [
                    {
                        "itemId": item.get("itemId"),
                        "itemName": item.get("itemName"),
                        "quantity": item.get("quantity")
                    }
                    for item in items
                ]
            }
            
            record = {
                "bin_id": bin_id,
                "bin_data": transformed_data
            }
            records.append(record)
        
        # Insert records in batches to avoid hitting request size limits
        batch_size = 100
        results = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            response = supabase.table("bin_count_records").upsert(batch).execute()
            results.append(response)
            
        return {
            "message": "Bin count data stored successfully",
            "total_records": len(records),
            "batches": len(results),
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"Error storing bin count data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing bin count data: {str(e)}")

async def fetch_bin_count_records() -> Dict[str, Any]:
    """
    Fetch bin count records from the bin_count_records table
    
    Returns:
        Dictionary with operation results and bin count records data
    """
    try:
        # Fetch records from bin_count_records table
        response = supabase.table("bin_count_records").select("*").execute()
        
        if not response.data:
            logger.info("No unprocessed bin records found in the database")
            return {
                "message": "No bin count records found",
                "total_records": 0,
                "data": []
            }
        
        # Log the first record for debugging
        if response.data:
            logger.info(f"First record structure: {response.data[0]}")
        
        # Return the data as is, without transformation
        return {
            "message": "Bin count records fetched successfully",
            "total_records": len(response.data),
            "data": [record["bin_data"] for record in response.data if "bin_data" in record]
        }
    
    except Exception as e:
        logger.error(f"Error fetching bin count records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching bin count records: {str(e)}") 