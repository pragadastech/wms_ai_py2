from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import oauth2_scheme, get_current_admin
from app.auth.models import UserCreate
from app.models.user import UserResponse
from app.database.supabase import supabase
from app.auth.utils import get_user_by_userid, pwd_ctx
from datetime import datetime
from jose import jwt
from app.config.settings import SECRET_KEY, ALGORITHM
from app.models.admin import AdminCreate
from app.models.response import DataResponse

router = APIRouter()

@router.get("/admin/dashboard")
async def get_admin_dashboard(current_admin: tuple = Depends(get_current_admin)):
    username, new_token = current_admin
    try:
        response = supabase.table("wms_ai_users").select("*").execute()
        total_users = len(response.data) if response.data else 0
        
        user_details = [
            {
                "userid": user["userid"],
                "email": user["email"],
                "created_at": user["created_at"]
            }
            for user in response.data
        ] if response.data else []
        
        return {
            "message": f"Welcome Admin {username}!",
            "total_users": total_users,
            "users": user_details,
            "new_token": new_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

def create_user(user: UserCreate) -> UserResponse:
    try:
        existing_user = get_user_by_userid(user.userid)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        hashed_password = pwd_ctx.hash(user.password)
        user_data = {
            "userid": user.userid,
            "email": user.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("wms_ai_users").insert(user_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
        return UserResponse(userid=user.userid, email=user.email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@router.post("/admin/register-user", response_model=UserResponse)
async def admin_register_user(user: UserCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type")
        if token_type != "admin":
            raise HTTPException(status_code=403, detail="Only admins can register users")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")
    
    return create_user(user)

@router.post("/admin/register", response_model=DataResponse)
async def register_admin(admin_data: AdminCreate):
    """
    Register a new admin user
    
    Args:
        admin_data: Admin registration data including username, company details, and password
        
    Returns:
        DataResponse with registration status and admin details
    """
    try:
        # Check if passwords match
        if admin_data.password != admin_data.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Passwords do not match"
            )
        
        # Check if username already exists
        existing_admin = supabase.table("master_admin_details").select("*").eq("username", admin_data.username).execute()
        if existing_admin.data:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )
        
        # Check if company email already exists
        existing_email = supabase.table("master_admin_details").select("*").eq("company_email", admin_data.company_email).execute()
        if existing_email.data:
            raise HTTPException(
                status_code=400,
                detail="Company email already registered"
            )
        
        # Check if phone number already exists
        existing_phone = supabase.table("master_admin_details").select("*").eq("phone_number", admin_data.phone_number).execute()
        if existing_phone.data:
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered"
            )
        
        # Hash the password
        hashed_password = pwd_ctx.hash(admin_data.password)
        
        # Prepare admin data
        admin_record = {
            "username": admin_data.username,
            "password": hashed_password,
            "company_name": admin_data.company_name,
            "company_email": admin_data.company_email,
            "phone_number": admin_data.phone_number,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert admin into database
        response = supabase.table("master_admin_details").insert(admin_record).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to register admin"
            )
        
        # Return success response without sensitive data
        return DataResponse(
            message="Admin registered successfully",
            total_records=1,
            data={
                "username": admin_data.username,
                "company_name": admin_data.company_name,
                "company_email": admin_data.company_email,
                "phone_number": admin_data.phone_number,
                "created_at": admin_record["created_at"]
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registering admin: {str(e)}"
        )