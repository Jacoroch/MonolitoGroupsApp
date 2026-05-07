import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

# Configuración de URLs (usando postgres-service)
def get_db_url(env_var, db_name):
    return os.getenv(env_var, f"postgresql://user_GA:password_db@postgres-service:5432/{db_name}")

AUTH_URL = get_db_url("AUTH_DB_URL", "auth_db")
GROUPS_URL = get_db_url("GROUPS_DB_URL", "groups_db")
MESSAGES_URL = get_db_url("MESSAGES_DB_URL", "messages_db")

engine_auth = create_engine(AUTH_URL)
engine_groups = create_engine(GROUPS_URL)
engine_messages = create_engine(MESSAGES_URL)

SessionLocalAuth = sessionmaker(autocommit=False, autoflush=False, bind=engine_auth)
SessionLocalGroups = sessionmaker(autocommit=False, autoflush=False, bind=engine_groups)
SessionLocalMessages = sessionmaker(autocommit=False, autoflush=False, bind=engine_messages)

Base = declarative_base()

def init_dbs():
    from modules.auth.models import User
    from modules.groups.models import Group, GroupMember
    from modules.messaging.models import Message, MessageRead, MessageReceipt

    retries = 5
    while retries > 0:
        try:
            print(f"🚀 Intentando conectar a las bases de datos... (Intentos restantes: {retries})")
            Base.metadata.create_all(bind=engine_auth, tables=[User.__table__])
            Base.metadata.create_all(bind=engine_groups, tables=[Group.__table__, GroupMember.__table__])
            Base.metadata.create_all(bind=engine_messages, tables=[
                Message.__table__, 
                MessageRead.__table__, 
                MessageReceipt.__table__
            ])
            print("✅ Conexión e inicialización exitosa!")
            break
        except OperationalError as e:
            retries -= 1
            if retries == 0:
                print("❌ No se pudo conectar a la DB tras 5 intentos. Abortando.")
                raise e
            print(f"⚠️ Base de datos no lista ({e}). Reintentando en 5s...")
            time.sleep(5)


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