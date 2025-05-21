import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
from requests_oauthlib import OAuth1
import logging
import sys
import time
from typing import Dict, Any, List
from pydantic import BaseModel, EmailStr, validator
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_operations.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Disable HTTP request logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("supabase").setLevel(logging.WARNING)

# =======================
# Load ENV Variables
# =======================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# NetSuite API credentials
NETSUITE_BASE_URL = "https://4809897-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
NETSUITE_CONSUMER_KEY = os.getenv("NETSUITE_CONSUMER_KEY")
NETSUITE_CONSUMER_SECRET = os.getenv("NETSUITE_CONSUMER_SECRET")
NETSUITE_TOKEN_ID = os.getenv("NETSUITE_TOKEN_ID")
NETSUITE_TOKEN_SECRET = os.getenv("NETSUITE_TOKEN_SECRET")
NETSUITE_ACCOUNT_ID = os.getenv("NETSUITE_ACCOUNT_ID")

# Add these constants after the existing constants
TOKEN_REFRESH_THRESHOLD = 5  # minutes before expiration to refresh
TOKEN_ACTIVITY_WINDOW = 30  # minutes of inactivity before requiring new login

# =======================
# Setup Supabase
# =======================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =======================
# FastAPI App Setup
# =======================
app = FastAPI()
# app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =======================
# User Models
# =======================
class UserCreate(BaseModel):
    userid: str
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserLogin(BaseModel):
    userid: str
    password: str

class UserResponse(BaseModel):
    userid: str
    email: str

# =======================
# Authentication Functions
# =======================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_ctx.verify(plain_password, hashed_password)

def get_admin_by_username(username: str):
    try:
        response = supabase.table("master_admin_details").select("*").eq("username", username).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching admin: {str(e)}")
        return None

def get_user_by_userid(userid: str):
    try:
        response = supabase.table("wms_ai_users").select("*").eq("userid", userid).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return None

def authenticate_user(userid: str, password: str):
    user = get_user_by_userid(userid)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

# =======================
# Token Management Functions
# =======================
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

# =======================
# Token Dependencies
# =======================
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

# =======================
# Routes
# =======================
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_admin_by_username(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"], "type": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin/dashboard")
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
        logger.error(f"Error fetching admin dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching dashboard data")

# --- User Management Functions ---
def create_user(user: UserCreate) -> UserResponse:
    """
    Create a new user in the database
    """
    try:
        # Check if user already exists
        existing_user = get_user_by_userid(user.userid)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )
        
        # Hash the password
        hashed_password = pwd_ctx.hash(user.password)
        
        # Create user data
        user_data = {
            "userid": user.userid,
            "email": user.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert user into database
        response = supabase.table("wms_ai_users").insert(user_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create user"
            )
            
        return UserResponse(
            userid=user.userid,
            email=user.email
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

# --- End User Management Functions ---

@app.post("/admin/register-user", response_model=UserResponse)
async def admin_register_user(user: UserCreate, token: str = Depends(oauth2_scheme)):
    """
    Admin endpoint to register new users
    """
    try:
        # Verify admin token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type")
        if token_type != "admin":
            raise HTTPException(status_code=403, detail="Only admins can register users")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")
    
    return create_user(user)

# --- Supabase helper functions ---
def clear_supabase_table(table_name: str) -> None:
    """
    Clear all data from a specified Supabase table.
    """
    try:
        logger.info(f"Clearing data from {table_name} table...")
        
        # Handle different table structures
        if table_name == "netsuite_locations":
            response = supabase.table(table_name).delete().neq("location_id", "0").execute()
        else:
            response = supabase.table(table_name).delete().neq("internal_id", "0").execute()
            
        logger.info(f"Successfully cleared {table_name} table")
    except Exception as e:
        logger.error(f"Error clearing {table_name} table: {str(e)}")
        raise

# --- End Supabase helper functions ---

@app.get("/netsuite/locations")
async def get_netsuite_locations(token: str = Depends(oauth2_scheme)):
    """
    Fetch all location data from NetSuite API, store it in Supabase, and display it in the console
    """
    try:
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    start_time = time.time()
    session = requests.Session()
    
    try:
        # Set up OAuth1 authentication
        auth = OAuth1(
            NETSUITE_CONSUMER_KEY,
            NETSUITE_CONSUMER_SECRET,
            NETSUITE_TOKEN_ID,
            NETSUITE_TOKEN_SECRET,
            signature_method="HMAC-SHA256",
            realm=NETSUITE_ACCOUNT_ID,
        )

        headers = {"Content-Type": "application/json"}
        
        # First, get the total pages from the initial request
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_locations&page_size=1000&page_number=1"
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Successfully connected to NetSuite API")
            
            if "summary" in data and "total_pages" in data["summary"]:
                total_pages = data["summary"]["total_pages"]
                total_records = data["summary"]["total_records"]
                logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
                
                all_locations_data = {}
                
                # Fetch data from all pages
                for page in range(1, total_pages + 1):
                    page_start_time = time.time()
                    logger.info(f"Fetching page {page}/{total_pages}...")
                    
                    page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_locations&page_size=1000&page_number={page}"
                    page_response = session.get(page_url, auth=auth, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if "data" in page_data:
                            all_locations_data.update(page_data["data"])
                            logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                        else:
                            logger.warning(f"No data found in page {page}")
                    else:
                        logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                if all_locations_data:
                    # Clear existing data and store new data in Supabase
                    logger.info("Clearing existing data and storing new data in Supabase...")
                    store_start_time = time.time()
                    
                    # Clear existing data
                    clear_supabase_table("netsuite_locations")
                    
                    # Prepare data for Supabase
                    supabase_data = [
                        {
                            "location_id": location_id,
                            "location_data": location_data
                        }
                        for location_id, location_data in all_locations_data.items()
                    ]
                    
                    # Store data in chunks to avoid hitting Supabase limits
                    chunk_size = 1000
                    successful_operations = 0
                    
                    for i in range(0, len(supabase_data), chunk_size):
                        chunk = supabase_data[i:i + chunk_size]
                        try:
                            # Upsert the data (insert or update if exists)
                            response = supabase.table("netsuite_locations").upsert(chunk).execute()
                            successful_operations += len(chunk)
                            logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
                        except Exception as e:
                            logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                    
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
                        "data": all_locations_data
                    }
                else:
                    logger.warning("No data was successfully fetched from any page")
                    raise HTTPException(
                        status_code=404,
                        detail="No data was successfully fetched from any page"
                    )
            else:
                logger.warning("No summary information found in API response")
                raise HTTPException(
                    status_code=404,
                    detail="No summary information found in API response"
                )
        else:
            logger.error(f"NetSuite API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NetSuite API error: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Exception during NetSuite API fetch: {str(e)}"
        )
    finally:
        # Close the session
        session.close()

@app.get("/netsuite/users")
async def get_netsuite_users(token: str = Depends(oauth2_scheme)):
    """
    Fetch all user data from NetSuite API, store it in Supabase, and display it in the console
    """
    try:
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    start_time = time.time()
    session = requests.Session()
    
    try:
        # Set up OAuth1 authentication
        auth = OAuth1(
            NETSUITE_CONSUMER_KEY,
            NETSUITE_CONSUMER_SECRET,
            NETSUITE_TOKEN_ID,
            NETSUITE_TOKEN_SECRET,
            signature_method="HMAC-SHA256",
            realm=NETSUITE_ACCOUNT_ID,
        )

        headers = {"Content-Type": "application/json"}
        
        # First, get the total pages from the initial request
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_users&page_size=1000&page_number=1"
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Successfully connected to NetSuite API")
            
            if "summary" in data and "total_pages" in data["summary"]:
                total_pages = data["summary"]["total_pages"]
                total_records = data["summary"]["total_records"]
                logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
                
                all_users_data = {}
                
                # Fetch data from all pages
                for page in range(1, total_pages + 1):
                    page_start_time = time.time()
                    logger.info(f"Fetching page {page}/{total_pages}...")
                    
                    page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_users&page_size=1000&page_number={page}"
                    page_response = session.get(page_url, auth=auth, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if "data" in page_data:
                            all_users_data.update(page_data["data"])
                            logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                        else:
                            logger.warning(f"No data found in page {page}")
                    else:
                        logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                if all_users_data:
                    # Clear existing data and store new data in Supabase
                    logger.info("Clearing existing data and storing new data in Supabase...")
                    store_start_time = time.time()
                    
                    # Clear existing data
                    clear_supabase_table("netsuite_users")
                    
                    # Prepare data for Supabase
                    supabase_data = [
                        {
                            "internal_id": user_id,
                            "user_data": user_data
                        }
                        for user_id, user_data in all_users_data.items()
                    ]
                    
                    # Store data in chunks to avoid hitting Supabase limits
                    chunk_size = 1000
                    successful_operations = 0
                    
                    for i in range(0, len(supabase_data), chunk_size):
                        chunk = supabase_data[i:i + chunk_size]
                        try:
                            # Upsert the data (insert or update if exists)
                            response = supabase.table("netsuite_users").upsert(chunk).execute()
                            successful_operations += len(chunk)
                            logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
                        except Exception as e:
                            logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                    
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
                        "data": all_users_data
                    }
                else:
                    logger.warning("No data was successfully fetched from any page")
                    raise HTTPException(
                        status_code=404,
                        detail="No data was successfully fetched from any page"
                    )
            else:
                logger.warning("No summary information found in API response")
                raise HTTPException(
                    status_code=404,
                    detail="No summary information found in API response"
                )
        else:
            logger.error(f"NetSuite API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NetSuite API error: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Exception during NetSuite API fetch: {str(e)}"
        )
    finally:
        # Close the session
        session.close()

@app.get("/netsuite/bins")
async def get_netsuite_bins(token: str = Depends(oauth2_scheme)):
    """
    Fetch all bin data from NetSuite API, store it in Supabase, and display it in the console
    """
    try:
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    start_time = time.time()
    session = requests.Session()
    
    try:
        # Set up OAuth1 authentication
        auth = OAuth1(
            NETSUITE_CONSUMER_KEY,
            NETSUITE_CONSUMER_SECRET,
            NETSUITE_TOKEN_ID,
            NETSUITE_TOKEN_SECRET,
            signature_method="HMAC-SHA256",
            realm=NETSUITE_ACCOUNT_ID,
        )

        headers = {"Content-Type": "application/json"}
        
        # First, get the total pages from the initial request
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_bins&page_size=1000&page_number=1"
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Successfully connected to NetSuite API")
            
            if "summary" in data and "total_pages" in data["summary"]:
                total_pages = data["summary"]["total_pages"]
                total_records = data["summary"]["total_records"]
                logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
                
                all_bins_data = {}
                
                # Fetch data from all pages
                for page in range(1, total_pages + 1):
                    page_start_time = time.time()
                    logger.info(f"Fetching page {page}/{total_pages}...")
                    
                    page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_bins&page_size=1000&page_number={page}"
                    page_response = session.get(page_url, auth=auth, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if "data" in page_data:
                            all_bins_data.update(page_data["data"])
                            logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                        else:
                            logger.warning(f"No data found in page {page}")
                    else:
                        logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                if all_bins_data:
                    # Clear existing data and store new data in Supabase
                    logger.info("Clearing existing data and storing new data in Supabase...")
                    store_start_time = time.time()
                    
                    # Clear existing data
                    clear_supabase_table("netsuite_bins")
                    
                    # Prepare data for Supabase
                    supabase_data = [
                        {
                            "internal_id": bin_id,
                            "bin_data": bin_data
                        }
                        for bin_id, bin_data in all_bins_data.items()
                    ]
                    
                    # Store data in chunks to avoid hitting Supabase limits
                    chunk_size = 1000
                    successful_operations = 0
                    
                    for i in range(0, len(supabase_data), chunk_size):
                        chunk = supabase_data[i:i + chunk_size]
                        try:
                            # Upsert the data (insert or update if exists)
                            response = supabase.table("netsuite_bins").upsert(chunk).execute()
                            successful_operations += len(chunk)
                            logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
                        except Exception as e:
                            logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                    
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
                        "data": all_bins_data
                    }
                else:
                    logger.warning("No data was successfully fetched from any page")
                    raise HTTPException(
                        status_code=404,
                        detail="No data was successfully fetched from any page"
                    )
            else:
                logger.warning("No summary information found in API response")
                raise HTTPException(
                    status_code=404,
                    detail="No summary information found in API response"
                )
        else:
            logger.error(f"NetSuite API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NetSuite API error: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Exception during NetSuite API fetch: {str(e)}"
        )
    finally:
        # Close the session
        session.close()

@app.get("/netsuite/inventory")
async def get_netsuite_inventory(token: str = Depends(oauth2_scheme)):
    """
    Fetch all inventory data from NetSuite API, store it in Supabase, and display it in the console
    """
    try:
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    start_time = time.time()
    session = requests.Session()
    
    try:
        # Set up OAuth1 authentication
        auth = OAuth1(
            NETSUITE_CONSUMER_KEY,
            NETSUITE_CONSUMER_SECRET,
            NETSUITE_TOKEN_ID,
            NETSUITE_TOKEN_SECRET,
            signature_method="HMAC-SHA256",
            realm=NETSUITE_ACCOUNT_ID,
        )

        headers = {"Content-Type": "application/json"}
        
        # First, get the total pages from the initial request
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_inventory&page_size=1000&page_number=1"
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Successfully connected to NetSuite API")
            
            if "summary" in data and "total_pages" in data["summary"]:
                total_pages = data["summary"]["total_pages"]
                total_records = data["summary"]["total_records"]
                logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
                
                all_inventory_data = {}
                
                # Fetch data from all pages
                for page in range(1, total_pages + 1):
                    page_start_time = time.time()
                    logger.info(f"Fetching page {page}/{total_pages}...")
                    
                    page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_inventory&page_size=1000&page_number={page}"
                    page_response = session.get(page_url, auth=auth, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if "data" in page_data:
                            all_inventory_data.update(page_data["data"])
                            logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                        else:
                            logger.warning(f"No data found in page {page}")
                    else:
                        logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                if all_inventory_data:
                    # Clear existing data and store new data in Supabase
                    logger.info("Clearing existing data and storing new data in Supabase...")
                    store_start_time = time.time()
                    
                    # Clear existing data
                    clear_supabase_table("netsuite_inventory")
                    
                    # Prepare data for Supabase
                    supabase_data = [
                        {
                            "internal_id": item_id,
                            "inventory_data": item_data
                        }
                        for item_id, item_data in all_inventory_data.items()
                    ]
                    
                    # Store data in chunks to avoid hitting Supabase limits
                    chunk_size = 1000
                    successful_operations = 0
                    
                    for i in range(0, len(supabase_data), chunk_size):
                        chunk = supabase_data[i:i + chunk_size]
                        try:
                            # Upsert the data (insert or update if exists)
                            response = supabase.table("netsuite_inventory").upsert(chunk).execute()
                            successful_operations += len(chunk)
                            logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
                        except Exception as e:
                            logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                    
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
                        "data": all_inventory_data
                    }
                else:
                    logger.warning("No data was successfully fetched from any page")
                    raise HTTPException(
                        status_code=404,
                        detail="No data was successfully fetched from any page"
                    )
            else:
                logger.warning("No summary information found in API response")
                raise HTTPException(
                    status_code=404,
                    detail="No summary information found in API response"
                )
        else:
            logger.error(f"NetSuite API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NetSuite API error: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Exception during NetSuite API fetch: {str(e)}"
        )
    finally:
        # Close the session
        session.close()

@app.get("/netsuite/items")
async def get_netsuite_items(token: str = Depends(oauth2_scheme)):
    """
    Fetch all items data from NetSuite API, store it in Supabase, and display it in the console
    """
    try:
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    start_time = time.time()
    session = requests.Session()
    
    try:
        # Set up OAuth1 authentication
        auth = OAuth1(
            NETSUITE_CONSUMER_KEY,
            NETSUITE_CONSUMER_SECRET,
            NETSUITE_TOKEN_ID,
            NETSUITE_TOKEN_SECRET,
            signature_method="HMAC-SHA256",
            realm=NETSUITE_ACCOUNT_ID,
        )

        headers = {"Content-Type": "application/json"}
        
        # First, get the total pages from the initial request
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_items&page_size=1000&page_number=1"
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Successfully connected to NetSuite API")
            
            if "summary" in data and "total_pages" in data["summary"]:
                total_pages = data["summary"]["total_pages"]
                total_records = data["summary"]["total_records"]
                logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
                
                all_items_data = {}
                
                # Fetch data from all pages
                for page in range(1, total_pages + 1):
                    page_start_time = time.time()
                    logger.info(f"Fetching page {page}/{total_pages}...")
                    
                    page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_items&page_size=1000&page_number={page}"
                    page_response = session.get(page_url, auth=auth, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if "data" in page_data:
                            all_items_data.update(page_data["data"])
                            logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                        else:
                            logger.warning(f"No data found in page {page}")
                    else:
                        logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                if all_items_data:
                    # Clear existing data and store new data in Supabase
                    logger.info("Clearing existing data and storing new data in Supabase...")
                    store_start_time = time.time()
                    
                    # Clear existing data
                    clear_supabase_table("netsuite_items")
                    
                    # Prepare data for Supabase
                    supabase_data = [
                        {
                            "internal_id": item_id,
                            "item_data": item_data
                        }
                        for item_id, item_data in all_items_data.items()
                    ]
                    
                    # Store data in chunks to avoid hitting Supabase limits
                    chunk_size = 1000
                    successful_operations = 0
                    
                    for i in range(0, len(supabase_data), chunk_size):
                        chunk = supabase_data[i:i + chunk_size]
                        try:
                            # Upsert the data (insert or update if exists)
                            response = supabase.table("netsuite_items").upsert(chunk).execute()
                            successful_operations += len(chunk)
                            logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
                        except Exception as e:
                            logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                    
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
                        "data": all_items_data
                    }
                else:
                    logger.warning("No data was successfully fetched from any page")
                    raise HTTPException(
                        status_code=404,
                        detail="No data was successfully fetched from any page"
                    )
            else:
                logger.warning("No summary information found in API response")
                raise HTTPException(
                    status_code=404,
                    detail="No summary information found in API response"
                )
        else:
            logger.error(f"NetSuite API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NetSuite API error: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Exception during NetSuite API fetch: {str(e)}"
        )
    finally:
        # Close the session
        session.close()

@app.get("/netsuite/sales-orders")
async def get_netsuite_sales_orders(token: str = Depends(oauth2_scheme)):
    """
    Fetch all sales orders data from NetSuite API, store it in Supabase, and display it in the console
    """
    try:
        # Verify JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    start_time = time.time()
    session = requests.Session()
    
    try:
        # Set up OAuth1 authentication
        auth = OAuth1(
            NETSUITE_CONSUMER_KEY,
            NETSUITE_CONSUMER_SECRET,
            NETSUITE_TOKEN_ID,
            NETSUITE_TOKEN_SECRET,
            signature_method="HMAC-SHA256",
            realm=NETSUITE_ACCOUNT_ID,
        )

        headers = {"Content-Type": "application/json"}
        
        # First, get the total pages from the initial request
        initial_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_salesOrders&page_size=1000&page_number=1"
        response = session.get(initial_url, auth=auth, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Successfully connected to NetSuite API")
            
            if "summary" in data and "total_pages" in data["summary"]:
                total_pages = data["summary"]["total_pages"]
                total_records = data["summary"]["total_records"]
                logger.info(f"Total Records: {total_records}, Total Pages: {total_pages}")
                
                all_sales_orders_data = {}
                
                # Fetch data from all pages
                for page in range(1, total_pages + 1):
                    page_start_time = time.time()
                    logger.info(f"Fetching page {page}/{total_pages}...")
                    
                    page_url = f"{NETSUITE_BASE_URL}?script=1758&deploy=1&action=get_salesOrders&page_size=1000&page_number={page}"
                    page_response = session.get(page_url, auth=auth, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if "data" in page_data:
                            all_sales_orders_data.update(page_data["data"])
                            logger.info(f"Successfully fetched page {page} in {time.time() - page_start_time:.2f} seconds")
                        else:
                            logger.warning(f"No data found in page {page}")
                    else:
                        logger.error(f"Error fetching page {page}: {page_response.status_code} - {page_response.text}")
                    
                    # Add a small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                if all_sales_orders_data:
                    # Clear existing data and store new data in Supabase
                    logger.info("Clearing existing data and storing new data in Supabase...")
                    store_start_time = time.time()
                    
                    # Clear existing data
                    clear_supabase_table("netsuite_sales_orders")
                    
                    # Prepare data for Supabase
                    supabase_data = [
                        {
                            "internal_id": order_id,
                            "sales_order_data": order_data
                        }
                        for order_id, order_data in all_sales_orders_data.items()
                    ]
                    
                    # Store data in chunks to avoid hitting Supabase limits
                    chunk_size = 1000
                    successful_operations = 0
                    
                    for i in range(0, len(supabase_data), chunk_size):
                        chunk = supabase_data[i:i + chunk_size]
                        try:
                            # Upsert the data (insert or update if exists)
                            response = supabase.table("netsuite_sales_orders").upsert(chunk).execute()
                            successful_operations += len(chunk)
                            logger.info(f"Successfully stored chunk {i//chunk_size + 1} in Supabase")
                        except Exception as e:
                            logger.error(f"Error storing chunk {i//chunk_size + 1} in Supabase: {str(e)}")
                    
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
                        "data": all_sales_orders_data
                    }
                else:
                    logger.warning("No data was successfully fetched from any page")
                    raise HTTPException(
                        status_code=404,
                        detail="No data was successfully fetched from any page"
                    )
            else:
                logger.warning("No summary information found in API response")
                raise HTTPException(
                    status_code=404,
                    detail="No summary information found in API response"
                )
        else:
            logger.error(f"NetSuite API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"NetSuite API error: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Exception during NetSuite API fetch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Exception during NetSuite API fetch: {str(e)}"
        )
    finally:
        # Close the session
        session.close()

# Update the response model
class DataResponse(BaseModel):
    status: int = 200
    message: str
    total_records: int
    data: Dict[str, Any]
    progress: Dict[str, Any] = None

# =======================
# User Routes
# =======================
@app.post("/user/login")
async def login_user(user: UserLogin):
    """
    Login user and return access token
    """
    user_data = authenticate_user(user.userid, user.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect userid or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_user_token(data={"sub": user_data["userid"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Get current user information
    """
    return UserResponse(
        userid=current_user["userid"],
        email=current_user["email"]
    )

# =======================
# Protected Routes with User Authentication
# =======================
@app.get("/data_locations", response_model=DataResponse)
async def get_data_locations(current_user: dict = Depends(get_current_user)):
    """
    Fetch all locations data from the database
    """
    try:
        all_locations, progress = await fetch_all_records("netsuite_locations")
        
        if all_locations:
            locations_data = {}
            for location in all_locations:
                locations_data[location["location_id"]] = location["location_data"]
            
            return {
                "status": 200,
                "message": "Data retrieved successfully",
                "total_records": len(all_locations),
                "data": locations_data,
                "progress": progress
            }
        else:
            raise HTTPException(status_code=404, detail="No locations data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data_bins", response_model=DataResponse)
async def get_data_bins(current_user: dict = Depends(get_current_user)):
    """
    Fetch all bins data from the database
    """
    try:
        all_bins, progress = await fetch_all_records("netsuite_bins")
        
        if all_bins:
            bins_data = {}
            for bin in all_bins:
                bins_data[bin["internal_id"]] = bin["bin_data"]
            
            return {
                "status": 200,
                "message": "Data retrieved successfully",
                "total_records": len(all_bins),
                "data": bins_data,
                "progress": progress
            }
        else:
            raise HTTPException(status_code=404, detail="No bins data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data_users", response_model=DataResponse)
async def get_data_users(current_user: dict = Depends(get_current_user)):
    """
    Fetch all users data from the database
    """
    try:
        all_users, progress = await fetch_all_records("netsuite_users")
        
        if all_users:
            users_data = {}
            for user in all_users:
                users_data[user["internal_id"]] = user["user_data"]
            
            return {
                "status": 200,
                "message": "Data retrieved successfully",
                "total_records": len(all_users),
                "data": users_data,
                "progress": progress
            }
        else:
            raise HTTPException(status_code=404, detail="No users data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data_inventory", response_model=DataResponse)
async def get_data_inventory(current_user: dict = Depends(get_current_user)):
    """
    Fetch all inventory data from the database
    """
    try:
        all_inventory, progress = await fetch_all_records("netsuite_inventory")
        
        if all_inventory:
            inventory_data = {}
            for item in all_inventory:
                internal_id = item["internal_id"]
                inventory_item_data = item["inventory_data"]
                
                # Extract the first item from the nested structure
                if "all" in inventory_item_data and "itemDetails" in inventory_item_data["all"] and inventory_item_data["all"]["itemDetails"]:
                    # Get the first item in the itemDetails array
                    first_item = inventory_item_data["all"]["itemDetails"][0]
                    # Store it directly under the internal_id
                    inventory_data[internal_id] = first_item
                else:
                    # In case the expected structure isn't found, store what we have
                    inventory_data[internal_id] = inventory_item_data
            
            return {
                "status": 200,
                "message": "Data retrieved successfully",
                "total_records": len(all_inventory),
                "data": inventory_data,
                "progress": progress
            }
        else:
            raise HTTPException(status_code=404, detail="No inventory data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data_items", response_model=DataResponse)
async def get_data_items(current_user: dict = Depends(get_current_user)):
    """
    Fetch all items data from the database
    """
    try:
        all_items, progress = await fetch_all_records("netsuite_items")
        
        if all_items:
            items_data = {}
            for item in all_items:
                items_data[item["internal_id"]] = item["item_data"]
            
            return {
                "status": 200,
                "message": "Data retrieved successfully",
                "total_records": len(all_items),
                "data": items_data,
                "progress": progress
            }
        else:
            raise HTTPException(status_code=404, detail="No items data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data_sales_orders", response_model=DataResponse)
async def get_data_sales_orders(current_user: dict = Depends(get_current_user)):
    """
    Fetch all sales orders data from the database
    """
    try:
        all_sales_orders, progress = await fetch_all_records("netsuite_sales_orders")
        
        if all_sales_orders:
            sales_orders_data = {}
            for order in all_sales_orders:
                sales_orders_data[order["internal_id"]] = order["sales_order_data"]
            
            return {
                "status": 200,
                "message": "Data retrieved successfully",
                "total_records": len(all_sales_orders),
                "data": sales_orders_data,
                "progress": progress
            }
        else:
            raise HTTPException(status_code=404, detail="No sales orders data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Add token refresh endpoint
@app.post("/refresh-token")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type: str = payload.get("type")
        last_activity = payload.get("last_activity")
        
        # Check if token is too old
        if last_activity:
            last_activity_time = datetime.fromtimestamp(last_activity)
            if (datetime.utcnow() - last_activity_time).total_seconds() > TOKEN_ACTIVITY_WINDOW * 60:
                raise HTTPException(
                    status_code=401,
                    detail="Session expired due to inactivity",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Create new token with updated expiration
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

# Update the pagination helper function with progress tracking
async def fetch_all_records(table_name: str, batch_size: int = 1000):
    """
    Fetch all records from a table using pagination with progress tracking
    """
    all_records = []
    offset = 0
    total_fetched = 0
    
    # First, get the total count of records
    try:
        count_response = supabase.table(table_name).select("count", count="exact").execute()
        total_count = count_response.count
    except Exception as e:
        logger.error(f"Error getting total count from {table_name}: {str(e)}")
        total_count = None
    
    while True:
        try:
            # Get current batch
            response = supabase.table(table_name).select("*").range(offset, offset + batch_size - 1).execute()
            
            if not response.data:
                break
                
            # Update progress
            total_fetched += len(response.data)
            progress = {
                "fetched": total_fetched,
                "total": total_count,
                "percentage": round((total_fetched / total_count * 100) if total_count else 0, 2),
                "current_batch": len(response.data),
                "batch_size": batch_size
            }
            
            # Log progress
            logger.info(f"Fetching {table_name}: {progress['percentage']}% complete ({total_fetched}/{total_count})")
            
            all_records.extend(response.data)
            
            if len(response.data) < batch_size:
                break
                
            offset += batch_size
            
        except Exception as e:
            logger.error(f"Error fetching records from {table_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching records: {str(e)}")
    
    return all_records, progress
