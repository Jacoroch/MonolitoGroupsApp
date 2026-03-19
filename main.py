from fastapi import FastAPI
from core.database import engine, Base

# --- Importación de modelos (SQLAlchemy DDL) ---
from modules.auth import models as auth_models
from modules.groups import models as groups_models         
from modules.messaging import models as messaging_models   

# --- Importación de enrutadores (Routers) ---
from modules.auth.router import router as auth_router
from modules.groups.router import router as groups_router
from modules.messaging.router import router as messaging_router
# --- Importación de manejo de archivos (pdf, imagenes, etc) ---
from fastapi.staticfiles import StaticFiles 

# Ejecución DDL: Crea las tablas si no existen en PostgreSQL
Base.metadata.create_all(bind=engine)

# Instanciación de la aplicación FastAPI
app = FastAPI(title="GroupsApp API", version="1.0")

# --- Servir archivos estáticos ---
# Esto permite que si alguien visita /static/foto.jpg, el servidor le entregue el archivo
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# --- Registro de sub-aplicaciones (Routers) ---
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(messaging_router)  # Integración del nuevo módulo WebSocket

# --- Endpoint REST de verificación de estado (Health Check) ---
@app.get("/")
async def root():
    return {"mensaje": "¡El monolito de GroupsApp está en línea y la base de datos está conectada!"}