from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserOut

class PostBase(BaseModel):
    content: str
    photo: Optional[str] = None
    profile_user_id: Optional[int] = None
    thread_id: Optional[int] = None

class PostCreate(PostBase):
    pass


class PostOut(PostBase):
    post_id: int
    date_created: datetime
    user: UserOut

    class Config:
        orm_mode = True
