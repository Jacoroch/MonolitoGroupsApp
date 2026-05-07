from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_dbs

from modules.auth.router import router as auth_router
from modules.groups.router import router as groups_router
from modules.messaging.router import router as messaging_router

app = FastAPI(
    title="GroupsApp API Gateway",
    version="1.0"
)

# 🚀 Inicializar bases
@app.on_event("startup")
def on_startup():
    print("🚀 Inicializando bases de datos...")
    init_dbs()

# 🌐 CORS (Configuración robusta para desarrollo)
# Añadimos 127.0.0.1 para evitar bloqueos si Next.js usa la IP en lugar del nombre
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Archivos estáticos (Asegúrate de que la carpeta 'uploads' exista)
# Nota: Si no existe la carpeta, la app dará error al iniciar.
import os
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/static", StaticFiles(directory="uploads"), name="static")

# 🔌 Routers
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(messaging_router)

@app.get("/")
def read_root():
    return {"message": "GroupsApp API is running 🚀"}