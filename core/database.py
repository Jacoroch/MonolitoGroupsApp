from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de conexión a tu base de datos local PostgreSQL
# Formato: postgresql://usuario:contraseña@servidor:puerto/nombre_base_de_datos
# TODO: Cambia 'postgres' y 'tu_password' por tus credenciales reales
SQLALCHEMY_DATABASE_URL = "postgresql://admin_groupsapp:root1234@db:5432/groupsapp_db"

# 1. El Engine es el motor que se comunica directamente con PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 2. SessionLocal será la fábrica que nos dará conexiones a la BD para cada petición
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base es la clase de la cual heredarán todos nuestros modelos (tablas)
Base = declarative_base()

# 4. Esta función nos servirá para inyectar la base de datos en nuestros endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()