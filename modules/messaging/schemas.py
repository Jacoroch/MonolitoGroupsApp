from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

# Schema para los recibos de lectura (viven en la misma BD de mensajería)
class MessageReceiptResponse(BaseModel):
    user_id: int
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Schema principal de respuesta
class MessageResponse(BaseModel):
    id: int
    content: Optional[str] = None
    media_url: Optional[str] = None
    sender_id: int # ✅ Solo el ID, la identidad la resuelve el Gateway o el Front
    group_id: int  # ✅ Solo el ID
    created_at: datetime
    
    # ✅ Relación interna permitida
    receipts: List[MessageReceiptResponse] = [] 

    model_config = ConfigDict(from_attributes=True)

# Schema para recibir datos del frontend
class MessageCreate(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None