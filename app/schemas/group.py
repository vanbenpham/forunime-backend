from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .user import UserOut

class GroupCreate(BaseModel):
    group_name: str
    member_ids: List[int]

    model_config = {"from_attributes": True}

class GroupUpdate(BaseModel):
    group_name: Optional[str] = None
    add_member_ids: Optional[List[int]] = None
    remove_member_ids: Optional[List[int]] = None
    add_co_owner_ids: Optional[List[int]] = None
    remove_co_owner_ids: Optional[List[int]] = None

    model_config = {"from_attributes": True}

class GroupOut(BaseModel):
    group_id: int
    group_name: str
    owner: UserOut
    co_owners: List[UserOut]
    members: List[UserOut]
    date_created: datetime

    model_config = {"from_attributes": True}
