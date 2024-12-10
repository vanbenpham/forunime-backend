from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from .user import UserOut
from .group import GroupOut

class MessageOut(BaseModel):
    message_id: int
    content: str
    date_created: datetime
    sender: Optional[UserOut] = None
    receiver: Optional[UserOut] = None
    group: Optional[GroupOut] = None
    deleted_for_receiver: bool = False

    model_config = {"from_attributes": True}

class MessageCreate(BaseModel):
    content: str
    receiver_id: Optional[int] = None
    group_id: Optional[int] = None

    model_config = {"from_attributes": True}

class MessageUpdate(BaseModel):
    content: Optional[str] = None

    model_config = {"from_attributes": True}
