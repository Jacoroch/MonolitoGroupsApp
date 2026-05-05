from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=True) 
    media_url = Column(String(500), nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ Referencias LÓGICAS (Soft Links)
    # Reemplazamos los ForeignKey por simples enteros indexados para búsquedas rápidas.
    sender_id = Column(Integer, index=True, nullable=False)
    group_id = Column(Integer, index=True, nullable=False)

    # ❌ ELIMINADO: sender = relationship("User")
    # ❌ ELIMINADO: group = relationship("Group")


class MessageRead(Base):
    __tablename__ = "message_reads"

    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ Relación FÍSICA permitida (porque 'messages' vive en esta misma base de datos)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # ✅ Referencia LÓGICA al usuario (porque Auth vive en otra BD)
    user_id = Column(Integer, index=True, nullable=False)
    
    read_at = Column(DateTime, default=datetime.utcnow)

    # ✅ Mantenemos esta relación porque es interna
    message = relationship("Message", backref="read_receipts")
    
    # ❌ ELIMINADO: user = relationship("User")


class MessageReceipt(Base):
    __tablename__ = "message_receipts"

    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ Relación FÍSICA permitida
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # ✅ Referencia LÓGICA al usuario (receptor)
    user_id = Column(Integer, index=True, nullable=False)
    
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # ✅ Mantenemos esta relación porque es interna
    message = relationship("Message", backref="receipts")
    
    # ❌ ELIMINADO: user = relationship("User")