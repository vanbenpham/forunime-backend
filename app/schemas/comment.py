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
    post_id: Optional[int] = None
    review_id: Optional[int] = None
    rate: Optional[int] = None  # Add this line


class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: Optional[str] = None
    photo: Optional[str] = None
    rate: Optional[int] = None  # Add this line


class CommentOut(BaseModel):
    comment_id: int
    content: str
    photo: Optional[str] = None
    date_created: datetime
    user_id: int
    user: UserOut
    parent_comment_id: Optional[int] = None
    replies: List['CommentOut'] = []
    post_id: Optional[int] = None
    review_id: Optional[int] = None
    rate: Optional[int] = None  # Add this line

    class Config:
        orm_mode = True


CommentOut.update_forward_refs()
