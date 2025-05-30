from fastapi import APIRouter, Depends, Body
from app.auth.dependencies import get_current_user
from app.models.user import UserResponse
from app.database.supabase import fetch_all_records, supabase
from app.models.response import DataResponse
from fastapi import HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import jwt
from app.config.settings import SECRET_KEY, ALGORITHM

router = APIRouter()

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminRegisterRequest(BaseModel):
    username: str
    company_email: str
    company_name: str
    password: str
    confirm_password: str
    phone_number: str

@router.get("/user/me", response_model=UserResponse)
async def read_users_me(current_user: tuple = Depends(get_current_user)):
    userid, _ = current_user
    from app.auth.utils import get_user_by_userid
    user_data = get_user_by_userid(userid)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(userid=user_data["userid"], email=user_data["email"])

@router.get("/data_locations", response_model=DataResponse)
async def get_data_locations(current_user: tuple = Depends(get_current_user)):
    try:
        all_locations, progress = await fetch_all_records("netsuite_locations")
        if all_locations:
            locations_data = {location["location_id"]: location["location_data"] for location in all_locations}
            return DataResponse(
                message="Data retrieved successfully",
                total_records=len(all_locations),
                data=locations_data,
                progress=progress
            )
        raise HTTPException(status_code=404, detail="No locations data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/data_bins", response_model=DataResponse)
async def get_data_bins(current_user: tuple = Depends(get_current_user)):
    try:
        all_bins, progress = await fetch_all_records("sql_netsuite_bins")
        if all_bins:
            bins_data = {
                bin["internal_id"]: {
                    "bin_number": bin["bin_number"],
                    "location": bin["location"],
                    "memo": bin["memo"],
                    "bin_orientation": bin["bin_orientation"],
                    "aisle_no": bin["aisle_no"],
                    "bin": bin["bin"],
                    "inactive_bin": bin["inactive_bin"],
                    "inventory_counted": bin["inventory_counted"],
                    "room": bin["room"],
                    "wh": bin["wh"]
                }
                for bin in all_bins
            }
            return DataResponse(
                message="Data retrieved successfully",
                total_records=len(all_bins),
                data=bins_data,
                progress=progress
            )
        raise HTTPException(status_code=404, detail="No bins data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/data_users", response_model=DataResponse)
async def get_data_users(current_user: tuple = Depends(get_current_user)):
    try:
        all_users, progress = await fetch_all_records("netsuite_users")
        if all_users:
            users_data = {user["internal_id"]: user["user_data"] for user in all_users}
            return DataResponse(
                message="Data retrieved successfully",
                total_records=len(all_users),
                data=users_data,
                progress=progress
            )
        raise HTTPException(status_code=404, detail="No users data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/data_inventory", response_model=DataResponse)
async def get_data_inventory(current_user: tuple = Depends(get_current_user)):
    try:
        all_inventory, progress = await fetch_all_records("sql_netsuite_inventory")
        if all_inventory:
            # Format the inventory data with the correct fields
            inventory_data = {}
            
            for item in all_inventory:
                internal_id = item["internal_id"]
                inventory_data[internal_id] = {
                    "item": item["item"],
                    "bin_number": item["bin_number"],
                    "location": item["location"],
                    "status": item["status"],
                    "on_hand": item["on_hand"],
                    "available": item["available"]
                }
            
            return DataResponse(
                message="Data retrieved successfully",
                total_records=len(all_inventory),
                data=inventory_data,
                progress=progress
            )
        raise HTTPException(status_code=404, detail="No inventory data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/data_items", response_model=DataResponse)
async def get_data_items(current_user: tuple = Depends(get_current_user)):
    try:
        all_items, progress = await fetch_all_records("sql_netsuite_items")
        if all_items:
            items_data = {
                item["internal_id"]: {
                    "name": item["name"],
                    "upc_code": item["upc_code"]
                }
                for item in all_items
            }
            return DataResponse(
                message="Data retrieved successfully",
                total_records=len(all_items),
                data=items_data,
                progress=progress
            )
        raise HTTPException(status_code=404, detail="No items data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/data_sales_orders", response_model=DataResponse)
async def get_data_sales_orders(current_user: tuple = Depends(get_current_user)):
    try:
        all_sales_orders, progress = await fetch_all_records("netsuite_sales_orders")
        if all_sales_orders:
            sales_orders_data = {order["internal_id"]: order["sales_order_data"] for order in all_sales_orders}
            return DataResponse(
                message="Data retrieved successfully",
                total_records=len(all_sales_orders),
                data=sales_orders_data,
                progress=progress
            )
        raise HTTPException(status_code=404, detail="No sales orders data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/wms-ai-users", response_model=DataResponse)
async def get_all_wms_ai_users(current_user: tuple = Depends(get_current_user)):
    """
    Fetch all users from the wms_ai_users table.
    """
    try:
        response = supabase.table("wms_ai_users").select("*").execute()
        users = response.data if response.data else []
        return DataResponse(
            message="Users retrieved successfully",
            total_records=len(users),
            data=[{
                "userid": user["userid"],
                "created_at": user["created_at"]
            } for user in users],
            progress=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@router.get("/master-admin-details", response_model=DataResponse)
async def get_master_admin_details():
    """
    Fetch all records from the master_admin_details table.
    """
    try:
        response = supabase.table("master_admin_details").select("*").execute()
        records = response.data if response.data else []
        return DataResponse(
            message="Master admin details retrieved successfully",
            total_records=len(records),
            data=[{
                "username": record["username"],
                "password": record["password"],
                "company_name": record["company_name"],
                "company_email": record["company_email"],
                "phone_number": record["phone_number"],
                "created_at": record["created_at"]
            } for record in records],
            progress=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching master admin details: {str(e)}")

@router.get("/user/authorized")
async def whoami(current_user: tuple = Depends(get_current_user)):
    """
    Return the username if logged in as admin, or userid if logged in as user, based on the token.
    """
    userid_or_username, token = current_user
    # Decode the token to get the type
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if token_type == "admin":
        return {"username": userid_or_username}
    else:
        return {"userid": userid_or_username}