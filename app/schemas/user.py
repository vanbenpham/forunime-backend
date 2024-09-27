from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    date_created: datetime
    profile_picture_url: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    username: str
    password: Optional[str] = None  # Make password optional