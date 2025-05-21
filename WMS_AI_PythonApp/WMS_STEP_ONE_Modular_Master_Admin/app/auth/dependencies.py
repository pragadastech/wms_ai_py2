from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.config.settings import SECRET_KEY, ALGORITHM, TOKEN_ACTIVITY_WINDOW
from app.auth.utils import create_access_token, create_user_token
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        last_activity = payload.get("last_activity")
        
        if username is None or token_type != "admin":
            raise credentials_exception
            
        if last_activity:
            last_activity_time = datetime.fromtimestamp(last_activity)
            if (datetime.utcnow() - last_activity_time).total_seconds() > TOKEN_ACTIVITY_WINDOW * 60:
                raise HTTPException(
                    status_code=401,
                    detail="Session expired due to inactivity",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        payload["last_activity"] = datetime.utcnow().timestamp()
        new_token = create_access_token(data={"sub": username, "type": "admin"})
        
        return username, new_token
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        userid: str = payload.get("sub")
        token_type: str = payload.get("type")
        last_activity = payload.get("last_activity")
        
        if userid is None or token_type not in ["user", "admin"]:
            raise credentials_exception
            
        if last_activity:
            last_activity_time = datetime.fromtimestamp(last_activity)
            if (datetime.utcnow() - last_activity_time).total_seconds() > TOKEN_ACTIVITY_WINDOW * 60:
                raise HTTPException(
                    status_code=401,
                    detail="Session expired due to inactivity",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        payload["last_activity"] = datetime.utcnow().timestamp()
        if token_type == "admin":
            new_token = create_access_token(data={"sub": userid, "type": "admin"})
        else:
            new_token = create_user_token(data={"sub": userid, "type": "user"})
        
        return userid, new_token
    except JWTError:
        raise credentials_exception