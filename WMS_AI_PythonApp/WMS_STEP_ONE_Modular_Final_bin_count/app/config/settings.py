import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# NetSuite API configuration
NETSUITE_BASE_URL = "https://4809897-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
NETSUITE_CONSUMER_KEY = os.getenv("NETSUITE_CONSUMER_KEY")
NETSUITE_CONSUMER_SECRET = os.getenv("NETSUITE_CONSUMER_SECRET")
NETSUITE_TOKEN_ID = os.getenv("NETSUITE_TOKEN_ID")
NETSUITE_TOKEN_SECRET = os.getenv("NETSUITE_TOKEN_SECRET")
NETSUITE_ACCOUNT_ID = os.getenv("NETSUITE_ACCOUNT_ID")

# Token management constants
TOKEN_REFRESH_THRESHOLD = 5  # minutes before expiration to refresh
TOKEN_ACTIVITY_WINDOW = 30  # minutes of inactivity before requiring new login