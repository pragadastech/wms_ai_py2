from supabase import create_client, Client
from fastapi import HTTPException
from app.config.settings import SUPABASE_URL, SUPABASE_KEY
from app.config.logging_config import setup_logging
from typing import Dict, List, Any

logger = setup_logging()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def store_bin_counts(bin_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Store bin count data in the bin_inventory table
    
    Args:
        bin_data: Dictionary with bin IDs as keys and arrays of items as values
        
    Returns:
        Dictionary with operation results
    """
    try:
        # Prepare records for insertion
        records = []
        for bin_id, items in bin_data.items():
            record = {
                "bin_id": bin_id,
                "bin_data": items  # Store the complete items array as JSONB
            }
            records.append(record)
        
        # Insert records in batches to avoid hitting request size limits
        batch_size = 100
        results = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            response = supabase.table("bin_inventory").upsert(batch).execute()
            results.append(response)
            
        return {
            "message": "Bin count data stored successfully",
            "total_records": len(records),
            "batches": len(results)
        }
    
    except Exception as e:
        logger.error(f"Error storing bin count data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing bin count data: {str(e)}") 