from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    userid: str
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 4:
            raise ValueError('Password must be at least 4 characters long')
        return v

class UserLogin(BaseModel):
    userid: str
    password: str