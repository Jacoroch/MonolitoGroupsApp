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

# Ejecución DDL: Crea las tablas si no existen en PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GroupsApp API", version="1.0")

# configurar templates
templates = Jinja2Templates(directory="templates")

# routers
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