from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import oauth2_scheme
from jose import jwt, JWTError
from app.config.settings import SECRET_KEY, ALGORITHM
from app.netsuite.operations import fetch_netsuite_data
from typing import Dict, Any

router = APIRouter()

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