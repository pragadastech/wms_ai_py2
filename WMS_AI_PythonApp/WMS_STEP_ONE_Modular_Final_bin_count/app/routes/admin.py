from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import oauth2_scheme, get_current_admin
from app.auth.models import UserCreate
from app.models.user import UserResponse
from app.database.supabase import supabase
from app.auth.utils import get_user_by_userid, pwd_ctx
from datetime import datetime
from jose import jwt
from app.config.settings import SECRET_KEY, ALGORITHM

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