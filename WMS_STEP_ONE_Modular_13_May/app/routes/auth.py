from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.utils import authenticate_admin, create_access_token, authenticate_user, create_user_token
from app.auth.models import UserLogin
from app.auth.dependencies import oauth2_scheme, get_current_admin, get_current_user
from jose import jwt, JWTError
from app.config.settings import SECRET_KEY, ALGORITHM, TOKEN_ACTIVITY_WINDOW
from datetime import datetime

router = APIRouter()

@router.post("/token", 
             summary="Admin Login",
             description="""
             Authenticate as an admin user and get an access token.
             
             **Example credential:**
             ```json
             {
               "username": "admin",
               "password": "admin123"
             }
             ```
             """)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_admin(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"], "type": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/user/login", 
             summary="Regular User Login",
             description="""
             Authenticate as a regular user and get an access token.
             
             **Example credential:**
             ```json
             {
               "userid": "user_123",
               "password": "User12345678"
             }
             ```
             """)
async def login_user(
    user: UserLogin = Body(
        ...,
        examples=[{
            "userid": "user_123",
            "password": "User12345678"
        }]
    )
):
    user_data = authenticate_user(user.userid, user.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect userid or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_user_token(data={"sub": user_data["userid"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh-token", 
             summary="Refresh Access Token",
             description="Refresh an existing token to extend its validity period.")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type")
        last_activity = payload.get("last_activity")
        
        if last_activity:
            last_activity_time = datetime.fromtimestamp(last_activity)
            if (datetime.utcnow() - last_activity_time).total_seconds() > TOKEN_ACTIVITY_WINDOW * 60:
                raise HTTPException(
                    status_code=401,
                    detail="Session expired due to inactivity",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        if token_type == "admin":
            new_token = create_access_token(data={"sub": payload.get("sub"), "type": "admin"})
        else:
            new_token = create_user_token(data={"sub": payload.get("sub"), "type": "user"})
            
        return {"access_token": new_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )