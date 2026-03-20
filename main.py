from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from core.database import engine, Base

# modelos
from modules.auth import models as auth_models
from modules.groups import models as groups_models
from modules.messaging import models as messaging_models

# routers
from modules.auth.router import router as auth_router
from modules.groups.router import router as groups_router
from modules.messaging.router import router as messaging_router
# --- Importación de manejo de archivos (pdf, imagenes, etc) ---
from fastapi.staticfiles import StaticFiles 

# Ejecución DDL: Crea las tablas si no existen en PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GroupsApp API", version="1.0")

# --- Servir archivos estáticos ---
# Esto permite que si alguien visita /static/foto.jpg, el servidor le entregue el archivo
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# --- Servir archivos estáticos ---
# Esto permite que si alguien visita /static/foto.jpg, el servidor le entregue el archivo
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# configurar templates
templates = Jinja2Templates(directory="templates")

# --- Registro de sub-aplicaciones (Routers) ---
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(messaging_router)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_view(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
def signup_view(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/chats", response_class=HTMLResponse)
def chats_view(request: Request):
    return templates.TemplateResponse("chats.html", {"request": request})

@app.get("/create-group", response_class=HTMLResponse)
def create_group_view(request: Request):
    return templates.TemplateResponse("create_group.html", {"request": request})

@app.get("/edit-group", response_class=HTMLResponse)
def create_group_view(request: Request):
    return templates.TemplateResponse("edit_group.html", {"request": request})