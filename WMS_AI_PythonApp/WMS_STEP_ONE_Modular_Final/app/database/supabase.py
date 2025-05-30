from supabase import create_client, Client
from fastapi import HTTPException
from app.config.settings import SUPABASE_URL, SUPABASE_KEY
from app.config.logging_config import setup_logging
import asyncio

logger = setup_logging()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clear_supabase_table(table_name: str) -> None:
    try:
        logger.info(f"Clearing data from {table_name} table...")
        if table_name == "netsuite_locations":
            response = supabase.table(table_name).delete().neq("location_id", "0").execute()
        else:
            response = supabase.table(table_name).delete().neq("internal_id", "0").execute()
        logger.info(f"Successfully cleared {table_name} table")
    except Exception as e:
        logger.error(f"Error clearing {table_name} table: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing table: {str(e)}")

async def fetch_all_records(table_name: str, batch_size: int = 500):
    all_records = []
    offset = 0
    total_fetched = 0
    
    try:
        count_response = supabase.table(table_name).select("count", count="exact").execute()
        total_count = count_response.count
        logger.info(f"Total records in {table_name}: {total_count}")
    except Exception as e:
        logger.error(f"Error getting total count from {table_name}: {str(e)}")
        total_count = None
    
    while True:
        try:
            # Add a small delay between requests to avoid rate limiting
            if offset > 0:
                await asyncio.sleep(0.1)
                
            response = supabase.table(table_name).select("*").range(offset, offset + batch_size - 1).execute()
            
            if not response.data:
                logger.info(f"No more data found at offset {offset}")
                break
                
            batch_records = response.data
            total_fetched += len(batch_records)
            
            progress = {
                "fetched": total_fetched,
                "total": total_count,
                "percentage": round((total_fetched / total_count * 100) if total_count else 0, 2),
                "current_batch": len(batch_records),
                "batch_size": batch_size,
                "current_offset": offset
            }
            
            logger.info(f"Fetching {table_name}: {progress['percentage']}% complete ({total_fetched}/{total_count})")
            all_records.extend(batch_records)
            
            if len(batch_records) < batch_size:
                logger.info(f"Received less records than batch size, ending fetch")
                break
                
            offset += batch_size
            
            # Safety check to prevent infinite loops
            if total_count and total_fetched >= total_count:
                logger.info(f"Reached total count of {total_count}, ending fetch")
                break
                
        except Exception as e:
            logger.error(f"Error fetching records from {table_name} at offset {offset}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching records: {str(e)}")
    
    logger.info(f"Completed fetching {total_fetched} records from {table_name}")
    return all_records, progress