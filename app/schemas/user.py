from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    profile_picture_url: str
    role: str
    date_created: str

    model_config = {"from_attributes": True}

    @validator('date_created', pre=True)
    def format_date(cls, value):
        return value.strftime('%Y-%m-%d')

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    profile_picture_url: Optional[str] = (
        'https://static.vecteezy.com/system/resources/thumbnails/009/292/244/small/default-avatar-icon-of-social-media-user-vector.jpg'
    )

    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

    model_config = {"from_attributes": True}

    @validator('password')
    def email_or_username_provided(cls, v, values):
        if not values.get('email') and not values.get('username'):
            raise ValueError('Either email or username must be provided')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = {"from_attributes": True}
