from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class AdminCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    company_name: constr(min_length=2, max_length=255)
    company_email: EmailStr
    phone_number: constr(min_length=10, max_length=20)
    password: constr(min_length=8)
    confirm_password: constr(min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "company_name": "Acme Corporation",
                "company_email": "john@acmecorp.com",
                "phone_number": "1234567890",
                "password": "securepass123",
                "confirm_password": "securepass123"
            }
        } 