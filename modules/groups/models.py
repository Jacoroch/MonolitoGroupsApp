from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

# ❌ ELIMINADO: from modules.auth.models import User

# 1. Tabla de Miembros (Convertida a Clase para facilitar consultas lógicas)
class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ Relación FÍSICA permitida (Apunta al grupo dentro de esta misma BD)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    
    # ✅ Referencia LÓGICA (Apunta al ID del usuario en el microservicio Auth)
    user_id = Column(Integer, index=True, nullable=False)
    
    # Un "bonus" útil para saber cuándo alguien se unió al grupo
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relación interna (permitida porque Group y GroupMember viven juntos)
    group = relationship("Group", back_populates="members")


# 2. Tabla principal de Grupos
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ✅ Referencia LÓGICA al administrador (Ya no es ForeignKey)
    admin_id = Column(Integer, index=True, nullable=False)

    # ✅ Relación interna hacia la tabla de miembros (pero NO hacia Users)
    members = relationship("GroupMember", back_populates="group")