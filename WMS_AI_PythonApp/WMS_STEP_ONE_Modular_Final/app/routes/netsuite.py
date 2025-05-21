from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from app.auth.dependencies import oauth2_scheme
from jose import jwt, JWTError
from app.config.settings import SECRET_KEY, ALGORITHM
from app.netsuite.operations import fetch_netsuite_data, send_bin_count_records_to_netsuite
from app.database.bin_operations import fetch_bin_count_records
from typing import Dict, Any, List
import logging
from app.database.supabase import supabase
from app.config.logging_config import setup_logging
import asyncio
from datetime import datetime, timedelta
import traceback

# Setup logger
logger = setup_logging()

router = APIRouter()

# Global variable to track the last processed record timestamp
last_processed_timestamp = None

async def process_new_records_background():
    """
    Background task to process new records
    """
    global last_processed_timestamp
    
    logger.info("Background task started")
    
    while True:
        try:
            # Get current timestamp
            current_time = datetime.utcnow()
            
            # If this is the first run, set last_processed_timestamp to 5 minutes ago
            if last_processed_timestamp is None:
                last_processed_timestamp = current_time - timedelta(minutes=5)
                logger.info(f"Initialized last_processed_timestamp to: {last_processed_timestamp}")
            
            logger.info(f"Checking for new records since: {last_processed_timestamp}")
            
            # Query for new records
            try:
                query = supabase.table("bin_count_records").select("*")
                
                # Add timestamp filter if we have a last processed timestamp
                if last_processed_timestamp:
                    query = query.gte("created_at", last_processed_timestamp.isoformat())
                
                response = query.execute()
                
                if response.data:
                    logger.info(f"Found {len(response.data)} new records to process")
                    logger.info(f"Records: {response.data}")
                    
                    # Process each record individually
                    for record in response.data:
                        try:
                            logger.info(f"Processing record: {record}")
                            
                            # Get bin_data from the record
                            bin_data = record.get("bin_data")
                            if not bin_data:
                                logger.warning(f"Record {record.get('bin_id')} has no bin_data field")
                                continue
                            
                            # If bin_data is a list, take the first item
                            if isinstance(bin_data, list):
                                logger.info(f"bin_data is a list, taking first item")
                                bin_data = bin_data[0] if bin_data else None
                            
                            if not bin_data:
                                logger.warning(f"Record {record.get('bin_id')} has empty bin_data")
                                continue
                            
                            # Check if bin_data is already in the correct format
                            if isinstance(bin_data, dict) and all(key in bin_data for key in ["action", "binId", "itemData", "location"]):
                                logger.info(f"Using raw bin_data as it's already properly formatted")
                                formatted_bin_data = bin_data
                            else:
                                # Create properly formatted bin_data
                                formatted_bin_data = {
                                    "action": "binCount",
                                    "binId": int(record["bin_id"]),
                                    "location": bin_data.get("locationId", 9),
                                    "itemData": [
                                        {
                                            "itemId": bin_data.get("itemId"),
                                            "quantity": bin_data.get("quantity", 0)
                                        }
                                    ]
                                }
                            
                            # Send to NetSuite
                            logger.info(f"Sending to NetSuite: {formatted_bin_data}")
                            result = await send_single_bin_to_netsuite(formatted_bin_data)
                            
                            # Update record status
                            update_data = {
                                "updated_at": "now()",
                                "netsuite_response": result,
                            }
                            
                            update_response = supabase.table("bin_count_records").update(update_data).eq("bin_id", record["bin_id"]).execute()
                            logger.info(f"Updated record {record['bin_id']} with result: {result}")
                            
                        except Exception as e:
                            logger.error(f"Error processing record {record.get('bin_id')}: {str(e)}")
                            logger.error(traceback.format_exc())
                            continue
                    
                    # Update last processed timestamp
                    last_processed_timestamp = current_time
                    logger.info(f"Updated last_processed_timestamp to: {last_processed_timestamp}")
                else:
                    logger.info("No new records found")
            
            except Exception as e:
                logger.error(f"Error querying database: {str(e)}")
                logger.error(traceback.format_exc())
            
            # Wait for 30 seconds before checking again
            logger.info("Waiting 30 seconds before next check...")
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in background task: {str(e)}")
            logger.error(traceback.format_exc())
            # Wait for 30 seconds before retrying
            await asyncio.sleep(30)

@router.on_event("startup")
async def startup_event():
    """
    Start the background task when the application starts
    """
    try:
        background_tasks = BackgroundTasks()
        background_tasks.add_task(process_new_records_background)
        logger.info("Started background task for processing new records")
    except Exception as e:
        logger.error(f"Error starting background task: {str(e)}")
        logger.error(traceback.format_exc())

async def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Verify the JWT token provided in the Authorization header.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        str: Username extracted from the token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")
    return username

@router.get("/netsuite/locations", 
            summary="Fetch Locations from NetSuite",
            description="""
            Retrieve all location data from NetSuite, store it in the database, and return the results.
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="Location data from NetSuite",
            response_model=Dict[str, Any])
async def get_netsuite_locations(_: str = Depends(verify_token)):
    """
    Fetch all location data from NetSuite and store it in the database.
    
    Returns:
        dict: Operation results and location data
    """
    return await fetch_netsuite_data("get_locations", "netsuite_locations")

@router.get("/netsuite/users", 
            summary="Fetch Users from NetSuite",
            description="""
            Retrieve all user data from NetSuite, store it in the database, and return the results.
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="User data from NetSuite",
            response_model=Dict[str, Any])
async def get_netsuite_users(_: str = Depends(verify_token)):
    """
    Fetch all user data from NetSuite and store it in the database.
    
    Returns:
        dict: Operation results and user data
    """
    return await fetch_netsuite_data("get_users", "netsuite_users")

@router.get("/netsuite/bins", 
            summary="Fetch Bins from NetSuite",
            description="""
            Retrieve all bin data from NetSuite, store it in the structured SQL table, and return the results.
            
            The bin data includes:
            - Bin number
            - Location
            - Bin orientation
            - Aisle number
            - Inactive status
            - And other bin attributes
            
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="Bin data from NetSuite",
            response_model=Dict[str, Any])
async def get_netsuite_bins(_: str = Depends(verify_token)):
    """
    Fetch all bin data from NetSuite and store it in the database.
    
    Returns:
        dict: Operation results and bin data
    """
    return await fetch_netsuite_data("get_bins", "sql_netsuite_bins")

@router.get("/netsuite/inventory", 
            summary="Fetch Inventory from NetSuite",
            description="""
            Retrieve all inventory data from NetSuite, store it in the structured SQL table, and return the results.
            
            The inventory data includes:
            - Item internal ID
            - Item name
            - Bin number
            - Location
            - Status
            - On-hand quantity
            - Available quantity
            
            Note: This endpoint processes a large amount of data and may take some time to complete.
            
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="Inventory data from NetSuite",
            response_model=Dict[str, Any])
async def get_netsuite_inventory(_: str = Depends(verify_token)):
    """
    Fetch all inventory data from NetSuite and store it in the database.
    
    Returns:
        dict: Operation results and inventory data
    """
    return await fetch_netsuite_data("get_inventory", "sql_netsuite_inventory")

@router.get("/netsuite/items", 
            summary="Fetch Items from NetSuite",
            description="""
            Retrieve all item data from NetSuite, store it in the structured SQL table, and return the results.
            
            The item data includes:
            - Internal ID
            - Item name
            - UPC code
            
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="Item data from NetSuite",
            response_model=Dict[str, Any])
async def get_netsuite_items(_: str = Depends(verify_token)):
    """
    Fetch all item data from NetSuite and store it in the database.
    
    Returns:
        dict: Operation results and item data
    """
    return await fetch_netsuite_data("get_items", "sql_netsuite_items")

@router.get("/netsuite/sales-orders", 
            summary="Fetch Sales Orders from NetSuite",
            description="""
            Retrieve all sales order data from NetSuite, store it in the database, and return the results.
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="Sales order data from NetSuite",
            response_model=Dict[str, Any])
async def get_netsuite_sales_orders(_: str = Depends(verify_token)):
    """
    Fetch all sales order data from NetSuite and store it in the database.
    
    Returns:
        dict: Operation results and sales order data
    """
    return await fetch_netsuite_data("get_salesOrders", "netsuite_sales_orders")

@router.post("/netsuite/single-bin", 
            summary="Send Single Bin to NetSuite",
            description="""
            Send a single bin record directly to NetSuite.
            
            This endpoint:
            1. Accepts a single bin record from the request body
            2. Sends it directly to NetSuite
            3. Returns the acknowledgment from NetSuite
            
            The data format to send in the request body:
            ```json
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
            ```
            
            This endpoint requires authentication with a valid JWT token.
            """,
            response_description="NetSuite acknowledgment for the bin record",
            response_model=Dict[str, Any])
async def send_single_bin_to_netsuite(
    bin_data: Dict[str, Any] = Body(..., 
        example={
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
    ),
    _: str = Depends(verify_token)
):
    """
    Send a single bin record directly to NetSuite.
    
    Args:
        bin_data: The bin inventory data to send to NetSuite
        
    Returns:
        dict: NetSuite acknowledgment and operation result
    """
    # Validate input data
    if "action" not in bin_data or bin_data["action"] != "binCount":
        raise HTTPException(status_code=400, detail="Invalid action or missing action field")
    
    if "binId" not in bin_data:
        raise HTTPException(status_code=400, detail="Missing binId field")
    
    if "location" not in bin_data:
        raise HTTPException(status_code=400, detail="Missing location field")
    
    if "itemData" not in bin_data or not isinstance(bin_data["itemData"], list) or len(bin_data["itemData"]) == 0:
        raise HTTPException(status_code=400, detail="Missing or invalid itemData field")
    
    # Validate item data
    for item in bin_data["itemData"]:
        if "itemId" not in item:
            raise HTTPException(status_code=400, detail="Missing itemId in itemData")
        if "quantity" not in item:
            raise HTTPException(status_code=400, detail="Missing quantity in itemData")
    
    try:
        # Send the bin data to NetSuite
        result = await send_bin_count_records_to_netsuite(bin_data)
        
        return {
            "message": "Bin data successfully sent to NetSuite",
            "bin_id": bin_data["binId"],
            "status": "success",
            "acknowledgment": result
        }
    except Exception as e:
        # Handle and return any errors
        return {
            "message": "Failed to send bin data to NetSuite",
            "bin_id": bin_data["binId"],
            "status": "failed",
            "error": str(e)
        }

@router.post("/bin-count", 
            summary="Send Bin Count Records to NetSuite",
            description="""
            Send bin count records to NetSuite and store the data in the database.
            
            This endpoint:
            1. Accepts bin count data in the request body
            2. Validates the input data
            3. Stores the data in the bin_count_records table
            4. Sends the data to NetSuite
            5. Updates the record with NetSuite's acknowledgment
            
            The data format to send in the request body:
            ```json
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
            ```
            """,
            response_description="NetSuite acknowledgment and operation results",
            response_model=Dict[str, Any])
async def send_bin_count(
    bin_data: Dict[str, Any] = Body(..., 
        example={
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
    ),
    _: str = Depends(verify_token)
):
    """
    Send bin count records to NetSuite and store in database.
    
    Args:
        bin_data: The bin inventory data to send to NetSuite
        
    Returns:
        dict: NetSuite acknowledgment and operation results
    """
    try:
        # Validate input data
        if "action" not in bin_data or bin_data["action"] != "binCount":
            raise HTTPException(status_code=400, detail="Invalid action or missing action field")
        
        if "binId" not in bin_data:
            raise HTTPException(status_code=400, detail="Missing binId field")
        
        if "location" not in bin_data:
            raise HTTPException(status_code=400, detail="Missing location field")
        
        if "itemData" not in bin_data or not isinstance(bin_data["itemData"], list) or len(bin_data["itemData"]) == 0:
            raise HTTPException(status_code=400, detail="Missing or invalid itemData field")
        
        # Validate item data
        for item in bin_data["itemData"]:
            if "itemId" not in item:
                raise HTTPException(status_code=400, detail="Missing itemId in itemData")
            if "quantity" not in item:
                raise HTTPException(status_code=400, detail="Missing quantity in itemData")
        
        # Store the data in the database first
        db_record = {
            "bin_id": str(bin_data["binId"]),
            "bin_data": bin_data,
            "created_at": "now()",
            "updated_at": "now()"
        }
        
        insert_response = supabase.table("bin_count_records").insert(db_record).execute()
        
        if not insert_response.data:
            raise HTTPException(status_code=500, detail="Failed to store record in database")
        
        logger.info(f"Stored bin count record in database: {db_record}")
        
        # Send to NetSuite
        netsuite_result = await send_bin_count_records_to_netsuite(bin_data)
        
        # Determine if the NetSuite operation was successful
        is_successful = False
        if isinstance(netsuite_result, dict):
            is_successful = netsuite_result.get("status") == "success"
        elif isinstance(netsuite_result, str):
            is_successful = "success" in netsuite_result.lower()
        
        # Update the record with NetSuite's acknowledgment
        update_data = {
            "updated_at": "now()",
            "netsuite_response": netsuite_result,
        }
        
        # Log the update data for debugging
        logger.info(f"Updating record with data: {update_data}")
        
        # Update the record
        update_response = supabase.table("bin_count_records").update(update_data).eq("bin_id", str(bin_data["binId"])).execute()
        
        # Verify the update was successful
        if not update_response.data:
            logger.error("Failed to update record in database")
            raise HTTPException(status_code=500, detail="Failed to update record in database")
        
        # Log the updated record
        logger.info(f"Updated record: {update_response.data[0]}")
        
        return {
            "message": "Bin count record stored and sent to NetSuite successfully",
            "bin_id": bin_data["binId"],
            "status": "success",
            "database_record": update_response.data[0],  # Return the updated record
            "netsuite_acknowledgment": netsuite_result,
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in send_bin_count: {str(e)}")
        return {
            "message": "Failed to store and send bin count record",
            "bin_id": bin_data.get("binId", "unknown"),
            "status": "failed",
            "error": str(e)
        }