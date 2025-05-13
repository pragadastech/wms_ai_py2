from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    userid: str
    email: EmailStr