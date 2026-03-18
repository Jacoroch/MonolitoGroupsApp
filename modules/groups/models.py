from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

# 1. Tabla intermedia para la relación Muchos-a-Muchos (Usuarios <-> Grupos)
group_members = Table(
    "group_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True),
)

# 2. Tabla principal de Grupos
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # El creador/administrador del grupo (Relación 1 a N con users)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Configuración de la relación para acceder fácilmente a los miembros desde el código
    members = relationship("User", secondary=group_members, backref="groups")