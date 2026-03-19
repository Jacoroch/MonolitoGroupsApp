from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MessageReceiptResponse(BaseModel):
    user_id: int
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    content: Optional[str]
    media_url: Optional[str]
    sender_id: int
    group_id: int
    created_at: datetime
    # Pydantic mapeará automáticamente el backref "receipts" a esta lista
    receipts: List[MessageReceiptResponse] = [] 

    class Config:
        from_attributes = True