from pydantic import BaseModel

class UserResponse(BaseModel):
    userid: str