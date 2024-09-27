from pydantic import BaseModel
from datetime import datetime

class ThreadBase(BaseModel):
    thread_name: str

class ThreadCreate(ThreadBase):
    pass

class ThreadOut(ThreadBase):
    thread_id: int
    date_created: datetime
    user_id: int

    class Config:
        orm_mode = True