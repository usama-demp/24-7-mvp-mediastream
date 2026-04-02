# app/schemas/user.py
from pydantic import BaseModel, EmailStr,ConfigDict

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password:str
    role:str

class UserResponse(UserCreate):
    id: int
    username: str
    email: EmailStr
    role:str

    class Config:
        model_config = ConfigDict(from_attributes=True)