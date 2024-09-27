from pydantic import BaseModel
from datetime import datetime

class CommentBase(BaseModel):
    content: str
    photo: str

class CommentCreate(CommentBase):
    pass


class CommentOut(CommentBase):
    post_id: int
    date_created: datetime
    user_id: int

    class Config:
        orm_mode = True