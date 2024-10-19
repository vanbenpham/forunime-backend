# schemas/comment.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, ForwardRef
from .user import UserOut

CommentOut = ForwardRef('CommentOut')

class CommentBase(BaseModel):
    content: str
    photo: Optional[str] = None
    parent_comment_id: Optional[int] = None
    post_id: int

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: Optional[str] = None
    photo: Optional[str] = None

class CommentOut(BaseModel):
    comment_id: int
    content: str
    photo: Optional[str] = None
    date_created: datetime
    user_id: int
    user: UserOut
    parent_comment_id: Optional[int] = None
    replies: List['CommentOut'] = []

    class Config:
        orm_mode = True

CommentOut.update_forward_refs()
