import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Obtenemos las 3 URLs (con valores por defecto por si acaso)
AUTH_URL = os.getenv("AUTH_DB_URL", "postgresql://user_GA:password_db@postgres:5432/auth_db")
GROUPS_URL = os.getenv("GROUPS_DB_URL", "postgresql://user_GA:password_db@postgres:5432/groups_db")
MESSAGES_URL = os.getenv("MESSAGES_DB_URL", "postgresql://user_GA:password_db@postgres:5432/messages_db")

# 2. Creamos 3 motores independientes
engine_auth = create_engine(AUTH_URL)
engine_groups = create_engine(GROUPS_URL)
engine_messages = create_engine(MESSAGES_URL)

# 3. Creamos 3 fábricas de sesiones
SessionLocalAuth = sessionmaker(autocommit=False, autoflush=False, bind=engine_auth)
SessionLocalGroups = sessionmaker(autocommit=False, autoflush=False, bind=engine_groups)
SessionLocalMessages = sessionmaker(autocommit=False, autoflush=False, bind=engine_messages)

Base = declarative_base()

# 4. Función de inicialización quirúrgica
def init_dbs():
    from modules.auth.models import User
    from modules.groups.models import Group, GroupMember
    from modules.messaging.models import Message, MessageRead, MessageReceipt

    # Le decimos a SQLAlchemy explícitamente qué tabla va en qué motor
    Base.metadata.create_all(bind=engine_auth, tables=[User.__table__])
    Base.metadata.create_all(bind=engine_groups, tables=[Group.__table__, GroupMember.__table__])
    Base.metadata.create_all(bind=engine_messages, tables=[
        Message.__table__, 
        MessageRead.__table__, 
        MessageReceipt.__table__
    ])

# 5. Dependencias para inyectar en FastAPI
def get_auth_db():
    db = SessionLocalAuth()
    try:
        yield db
    finally:
        db.close()

def get_groups_db():
    db = SessionLocalGroups()
    try:
        yield db
    finally:
        db.close()

def get_messaging_db():
    db = SessionLocalMessages()
    try:
        yield db
    finally:
        db.close()