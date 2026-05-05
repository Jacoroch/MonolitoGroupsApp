from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Inicializador de Bases de Datos separadas
from core.database import init_dbs

# Routers
from modules.auth.router import router as auth_router
from modules.groups.router import router as groups_router
from modules.messaging.router import router as messaging_router

app = FastAPI(title="GroupsApp API Gateway", version="1.0")

# Evento de inicio: Crea las tablas en sus respectivas bases de datos
@app.on_event("startup")
def on_startup():
    print("🚀 Arrancando API Gateway e inicializando bases de datos aisladas...")
    init_dbs()

# --- Servir archivos estáticos ---
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")

# --- Registro de sub-aplicaciones (Routers) ---
app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(messaging_router)


# --- VISTAS DEL FRONTEND (Temporal hasta la migración a React/Next.js) ---
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
def edit_group_view(request: Request):
    return templates.TemplateResponse("edit_group.html", {"request": request})