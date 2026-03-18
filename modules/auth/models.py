from sqlalchemy import Column, Integer, String, Boolean
from core.database import Base

class User(Base):
    __tablename__ = "users"

    # Definición de las columnas de la tabla
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    
    # ¡Nunca guardamos la contraseña en texto plano! 
    hashed_password = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)