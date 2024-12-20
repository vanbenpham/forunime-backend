# schemas/post.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .user import UserOut
from .comment import CommentOut

# schemas/post.py

class PostBase(BaseModel):
    content: str
    photo: Optional[str] = None
    profile_user_id: Optional[int] = None
    thread_id: Optional[int] = None  # Make thread_id optional

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None
    photo: Optional[str] = None
    profile_user_id: Optional[int] = None

class PostOut(PostBase):
    post_id: int
    date_created: datetime
    user_id: int
    user: UserOut
    comments: List[CommentOut] = []

    class Config:
        orm_mode = True

