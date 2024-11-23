# schemas/review.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserOut

class ReviewBase(BaseModel):
    name: str
    type: str  # e.g., anime, manga, novel
    description: str
    feedback: Optional[str] = None
    photo_url: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    feedback: Optional[str] = None
    photo_url: Optional[str] = None

class ReviewOut(ReviewBase):
    review_id: int
    date_created: datetime
    feedback_owner_id: int
    user: UserOut
    review_count: int
    average_rate: float  # Computed property

    class Config:
        orm_mode = True

