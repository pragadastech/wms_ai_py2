import time
import requests
from fastapi import HTTPException
from app.config.settings import NETSUITE_BASE_URL
from app.netsuite.client import get_netsuite_auth, with_retry
from app.database.supabase import clear_supabase_table
from app.config.logging_config import setup_logging

logger = setup_logging()

@with_retry(max_retries=3, base_delay=2, max_delay=30)
async def fetch_netsuite_data(action: str, table_name: str):
    """
    Fetches data from NetSuite API and stores it in the specified Supabase table.
    
    Includes:
    - Retry logic with exponential backoff
    - Circuit breaker pattern to prevent cascading failures
    - Comprehensive error handling and logging
    
    Args:
        action: The NetSuite API action to perform (e.g., 'get_bins', 'get_inventory')
        table_name: The name of the Supabase table where data will be stored
        
    Returns:
        dict: A dictionary containing operation results and statistics
        
    Raises:
        HTTPException: For API errors, connection issues, or data processing failures
    """
    start_time = time.time()
    session = requests.Session()
    auth = get_netsuite_auth()
    headers = {"Content-Type": "application/json"}
    
    try:
        # Build initial request URL
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action={action}&page_size=1000&page_number=1"
        logger.info(f"Making initial request to NetSuite API: {action}")
        
        # Make the initial request
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code != 200:
            error_message = f"NetSuite API error: {response.status_code} - {response.text}"
            logger.error(error_message)
            raise HTTPException(status_code=response.status_code, detail=error_message)
        
        # Parse the response
        data = response.json()
        logger.info("Successfully connected to NetSuite API")
        
        # Verify response contains expected structure
        if "summary" not in data or "total_pages" not in data["summary"]:
            error_message = "No summary information found in API response"
            logger.warning(error_message)
            raise HTTPException(status_code=404, detail=error_message)
        
        # Extract pagination information
        total_pages = data["summary"]["total_pages"]
        total_records = data["summary"]["total_records"]
        logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
        
        # Initialize container for all data
        all_data = {}
        
        # Fetch data from all pages
        for page in range(1, total_pages + 1):
            page_start_time = time.time()
            logger.info(f"Fetching page {page}/{total_pages}...")
            
            # Build page URL
            page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action={action}&page_size=1000&page_number={page}"
            
            # Make the request for this page
            page_response = session.get(page_url, auth=auth, headers=headers)
            
            if page_response.status_code == 200:
                page_data = page_response.json()
                if "data" in page_data:
                    all_data.update(page_data["data"])
                    logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                else:
                    logger.warning(f"No data found in page {page}")
            else:
                logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                if page_response.status_code >= 500:
                    # For server errors, raise exception to trigger retry logic
                    raise HTTPException(
                        status_code=page_response.status_code,
                        detail=f"NetSuite API server error: {page_response.text}"
                    )
            
            # Add a small delay between requests to avoid rate limiting
            # This could be dynamic based on response headers if API provides rate limit info
            time.sleep(0.5)
        
        # Check if we got any data
        if not all_data:
            error_message = "No data was successfully fetched from any page"
            logger.warning(error_message)
            raise HTTPException(status_code=404, detail=error_message)
        
        # Proceed with data storage
        logger.info("Clearing existing data and storing new data in Supabase...")
        store_start_time = time.time()
        
        # Clear existing data
        clear_supabase_table(table_name)
        
        # First, let's check the structure of the first item to understand the data
        if all_data:
            first_item_id, first_item_data = next(iter(all_data.items()))
            logger.info(f"First item structure - ID: {first_item_id}")
            logger.info(f"First item data type: {type(first_item_data)}")
            if isinstance(first_item_data, dict):
                logger.info(f"First item data keys: {list(first_item_data.keys())}")
        
        # Define the column mappings for each table
        table_columns = {
            "netsuite_locations": {
                "id": "location_id",
                "data": "location_data"
            },
            "netsuite_users": {
                "id": "internal_id",
                "data": "user_data"
            },
            "sql_netsuite_bins": {
                "id": "internal_id",
                "data": {
                    "bin_number": "bin_number",
                    "location": "location",
                    "memo": "memo",
                    "bin_orientation": "bin_orientation",
                    "aisle_no": "aisle_no",
                    "bin": "bin",
                    "inactive_bin": "inactive_bin",
                    "inventory_counted": "inventory_counted",
                    "room": "room",
                    "wh": "wh"
                }
            },
            "sql_netsuite_items": {
                "id": "internal_id",
                "data": {
                    "name": "name",
                    "upc_code": "upc_code"
                }
            },
            "sql_netsuite_inventory": {
                "id": "internal_id",
                "data": {
                    "item": "item",
                    "bin_number": "bin_number",
                    "location": "location",
                    "status": "status",
                    "on_hand": "on_hand",
                    "available": "available"
                }
            },
            "netsuite_bins": {
                "id": "internal_id",
                "data": "bin_data"
            },
            "netsuite_inventory": {
                "id": "internal_id",
                "data": "inventory_data"
            },
            "netsuite_items": {
                "id": "internal_id",
                "data": "item_data"
            },
            "netsuite_sales_orders": {
                "id": "internal_id",
                "data": "sales_order_data"
            }
        }
        
        if table_name not in table_columns:
            raise HTTPException(status_code=500, detail=f"Unknown table name: {table_name}")
            
        columns = table_columns[table_name]
        supabase_data = []
        
        if table_name == "sql_netsuite_inventory":
            # Special handling for the nested inventory data structure
            logger.info("Processing nested inventory data structure...")
            
            for item_id, locations in all_data.items():
                for location_id, location_data in locations.items():
                    if "itemDetails" in location_data and isinstance(location_data["itemDetails"], list):
                        for item_detail in location_data["itemDetails"]:
                            try:
                                record = {
                                    "internal_id": item_detail.get("internal_id", ""),
                                    "item": item_detail.get("item", ""),
                                    "bin_number": item_detail.get("bin_number", ""),
                                    "location": item_detail.get("location", ""),
                                    "status": item_detail.get("status", ""),
                                    "on_hand": item_detail.get("on_hand", "0"),
                                    "available": item_detail.get("available", "0")
                                }
                                supabase_data.append(record)
                            except Exception as e:
                                logger.error(f"Error processing inventory item {item_id} in location {location_id}: {str(e)}")
                                logger.error(f"Item detail: {item_detail}")
                                continue
            
            logger.info(f"Processed {len(supabase_data)} inventory records from nested structure")
        elif table_name == "netsuite_inventory":
            # Store flattened inventory data directly
            logger.info("Processing inventory data with flattened structure...")
            
            for item_id, locations in all_data.items():
                try:
                    # Extract first item from the nested structure
                    if "all" in locations and "itemDetails" in locations["all"] and locations["all"]["itemDetails"]:
                        # Get the first item in the itemDetails array
                        first_item = locations["all"]["itemDetails"][0]
                        # Store it directly as the data for this item_id
                        record = {
                            "internal_id": item_id,
                            "inventory_data": first_item
                        }
                        supabase_data.append(record)
                    else:
                        # Fallback if structure isn't as expected
                        record = {
                            "internal_id": item_id,
                            "inventory_data": locations
                        }
                        supabase_data.append(record)
                except Exception as e:
                    logger.error(f"Error processing inventory item {item_id}: {str(e)}")
                    logger.error(f"Item data: {locations}")
                    continue
            
            logger.info(f"Processed {len(supabase_data)} inventory records with flattened structure")
        else:
            # Standard processing for other table types
            for item_id, item_data in all_data.items():
                try:
                    if table_name == "sql_netsuite_bins":
                        # Transform the data for the new SQL table structure
                        record = {
                            "internal_id": item_id,
                            "bin_number": item_data.get("bin_number", ""),
                            "location": item_data.get("location", ""),
                            "memo": item_data.get("memo", ""),
                            "bin_orientation": item_data.get("bin_orentation", ""),  # Note: typo in API response
                            "aisle_no": item_data.get("aisle_no", ""),
                            "bin": item_data.get("bin", ""),
                            "inactive_bin": item_data.get("inactive_bin", False),
                            "inventory_counted": item_data.get("inventory_counted", False),
                            "room": item_data.get("room", ""),
                            "wh": item_data.get("wh", "")
                        }
                    elif table_name == "sql_netsuite_items":
                        # Transform the data for the new SQL items table structure
                        record = {
                            "internal_id": item_id,
                            "name": item_data.get("name", ""),
                            "upc_code": item_data.get("upc_code", "")
                        }
                    else:
                        # Create a record with the correct column names for the specific table
                        record = {
                            columns["id"]: item_id,
                            columns["data"]: item_data
                        }
                    supabase_data.append(record)
                except Exception as e:
                    logger.error(f"Error processing item {item_id}: {str(e)}")
                    logger.error(f"Item data: {item_data}")
                    continue
        
        if not supabase_data:
            raise HTTPException(status_code=500, detail="No valid data to store")
            
        # Log the structure of the first record to be stored
        if supabase_data:
            logger.info(f"First record to be stored: {supabase_data[0]}")
        
        chunk_size = 1000
        successful_operations = 0
        from app.database.supabase import supabase
        
        for i in range(0, len(supabase_data), chunk_size):
            chunk = supabase_data[i:i + chunk_size]
            try:
                # Log the structure of the first record in this chunk
                logger.info(f"Storing chunk {i//chunk_size + 1}, first record: {chunk[0]}")
                
                if table_name == "sql_netsuite_inventory":
                    # For inventory, use insert instead of upsert since we don't have a primary key
                    response = supabase.table(table_name).insert(chunk).execute()
                else:
                    # For other tables, continue using upsert
                    response = supabase.table(table_name).upsert(chunk).execute()
                
                successful_operations += len(chunk)
                logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
            except Exception as e:
                logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                logger.error(f"First record in failed chunk: {chunk[0] if chunk else 'No records'}")
                raise HTTPException(status_code=500, detail=f"Error storing data: {str(e)}")
        
        store_time = time.time() - store_start_time
        logger.info(f"Data storage completed in {store_time:.2f} seconds")
        
        return {
            "status": "success",
            "message": "Data fetched and stored successfully",
            "total_records": total_records,
            "total_pages": total_pages,
            "successful_operations": successful_operations,
            "fetching_time": time.time() - start_time - store_time,
            "storage_time": store_time,
            "total_processing_time": time.time() - start_time,
            "data": all_data
        }
    
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Exception during NetSuite API fetch: {str(e)}")
    finally:
        session.close()

@with_retry(max_retries=3, base_delay=2, max_delay=30)
async def send_bin_count_records_to_netsuite(bin_inventory_data):
    """
    Send bin count records to NetSuite
    
    Args:
        bin_inventory_data: Dictionary containing bin count records data with the format:
        {
          "action": "binCount",
          "location": location_id,
          "binId": bin_id,
          "itemData": [
              {
                "itemId": item_id,
                "quantity": quantity
              },
              ...
          ]
        }
        
    Returns:
        dict: A dictionary containing the NetSuite acknowledgment and operation results
        
    Raises:
        HTTPException: For API errors, connection issues, or data processing failures
    """
    start_time = time.time()
    session = requests.Session()
    auth = get_netsuite_auth()
    headers = {"Content-Type": "application/json"}
    
    try:
        # Build request URL for bin inventory update endpoint
        url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=update_bin_count_records"
        logger.info(f"Sending bin inventory data to NetSuite API")
        
        # Make the POST request
        response = session.post(url, auth=auth, headers=headers, json=bin_inventory_data)
        
        if response.status_code != 200:
            error_message = f"NetSuite API error: {response.status_code} - {response.text}"
            logger.error(error_message)
            raise HTTPException(status_code=response.status_code, detail=error_message)
        
        # Parse the response
        data = response.json()
        logger.info("Successfully sent bin inventory data to NetSuite API")
        
        # Return the acknowledgment from NetSuite along with operation details
        return {
            "message": "Bin inventory data successfully sent to NetSuite",
            "netsuite_acknowledgment": data,
            "operation_time": f"{time.time() - start_time:.2f} seconds"
        }
    
    except requests.RequestException as e:
        error_message = f"Error connecting to NetSuite API: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=503, detail=error_message)
    
    except Exception as e:
        error_message = f"Error processing bin inventory update: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=error_message) 