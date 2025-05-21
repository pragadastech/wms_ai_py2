from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, TOKEN_REFRESH_THRESHOLD, TOKEN_ACTIVITY_WINDOW
from app.database.supabase import supabase

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_ctx.verify(plain_password, hashed_password)

def get_user_by_userid(userid: str):
    try:
        response = supabase.table("wms_ai_users").select("*").eq("userid", userid).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

def authenticate_user(userid: str, password: str):
    user = get_user_by_userid(userid)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user

def authenticate_admin(username: str, password: str):
    response = supabase.table("admin_john").select("*").eq("username", username).execute()
    user = response.data
    if not user or not verify_password(password, user[0]["password"]):
        return None
    return user[0]

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "admin",
        "iat": datetime.utcnow(),
        "last_activity": datetime.utcnow().timestamp()
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_user_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "user",
        "iat": datetime.utcnow(),
        "last_activity": datetime.utcnow().timestamp()
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def should_refresh_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        if not exp:
            return False
        exp_time = datetime.fromtimestamp(exp)
        time_until_exp = exp_time - datetime.utcnow()
        return time_until_exp.total_seconds() < TOKEN_REFRESH_THRESHOLD * 60
    except JWTError:
        return False