from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Lo que recibimos del Frontend
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Lo que le respondemos al Frontend
class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    admin_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        
# Molde para añadir un miembro
class MemberAdd(BaseModel):
    user_id: int