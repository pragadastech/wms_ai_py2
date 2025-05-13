from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    userid: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    userid: str
    password: str