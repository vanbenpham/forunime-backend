# schemas/user.py

from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    date_created: str
    profile_picture_url: str

    class Config:
        orm_mode = True

    @validator('date_created', pre=True)
    def format_date(cls, value):
        return value.strftime('%Y-%m-%d')

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    profile_picture_url: str = (
        'https://static.vecteezy.com/system/resources/thumbnails/009/292/244/small/default-avatar-icon-of-social-media-user-vector.jpg'
    )

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

    @validator('password')
    def email_or_username_provided(cls, v, values, **kwargs):
        email = values.get('email')
        username = values.get('username')
        if not email and not username:
            raise ValueError('Either email or username must be provided')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    profile_picture_url: Optional[str] = None
