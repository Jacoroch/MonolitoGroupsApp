from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    
    # El contenido puede ser nulo si el usuario solo envía una foto sin texto
    content = Column(Text, nullable=True) 
    
    # ¡Aquí está la conexión con tu diagrama! Guardaremos la URL de S3
    media_url = Column(String(500), nullable=True) 
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Llaves foráneas para saber quién lo envió y a qué grupo pertenece
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

    # Relaciones lógicas (opcionales, pero muy útiles para FastAPI)
    sender = relationship("User")
    group = relationship("Group")

class MessageRead(Base):
    __tablename__ = "message_reads"

    id = Column(Integer, primary_key=True, index=True)
    
    # ¿A qué mensaje pertenece este "visto"?
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # ¿Quién fue la persona que lo vio?
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ¿A qué hora exacta lo vio? (Para los famosos dos chulitos azules)
    read_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones para facilitar consultas después
    message = relationship("Message", backref="read_receipts")
    user = relationship("User")

class MessageReceipt(Base):
    __tablename__ = "message_receipts"

    id = Column(Integer, primary_key=True, index=True)
    
    # ¿De qué mensaje estamos hablando?
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    
    # ¿A qué usuario (receptor) le pertenece este estado?
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # ¿Cuándo le llegó al dispositivo? (Doble chulito gris)
    # Es nullable=True porque al principio el mensaje aún no ha llegado
    delivered_at = Column(DateTime, nullable=True)
    
    # ¿Cuándo abrió el chat y lo leyó? (Doble chulito azul)
    # También es nullable=True por defecto
    read_at = Column(DateTime, nullable=True)

    # Relaciones
    message = relationship("Message", backref="receipts")
    user = relationship("User")