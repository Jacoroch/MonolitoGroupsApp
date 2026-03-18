from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageResponse(BaseModel):
    id: int
    content: Optional[str]
    media_url: Optional[str]
    sender_id: int
    group_id: int
    created_at: datetime

    class Config:
        from_attributes = True
