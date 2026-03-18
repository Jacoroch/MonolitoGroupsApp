from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose import JWTError, jwt
import bcrypt  
from fastapi import Query, WebSocketException, status
from core.database import get_db
from modules.auth import models, schemas

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# --- Configuración del Token ---
SECRET_KEY = "una_clave_super_secreta_y_larga_para_tu_proyecto"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# Esto le dice a FastAPI dónde debe ir la gente a conseguir su token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Este es nuestro guardia de seguridad
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Intentamos desencriptar el pase VIP
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Buscamos al usuario en la base de datos
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# --- Funciones Auxiliares de Encriptación ---
def hash_password(password: str) -> str:
    """Hashea la contraseña usando bcrypt de forma nativa"""
    # bcrypt requiere que la contraseña esté codificada en bytes
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash"""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Endpoints ---
# --- Register ---
@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado.")
    
    # Usamos nuestra nueva función para encriptar
    hashed_password = hash_password(user.password)
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# --- Login ---
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # Usamos nuestra nueva función para verificar
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

# --- Adaptar la Validación JWT para WebSockets
async def get_current_user_ws(
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    """Dependencia específica para validar JWT en conexiones WebSocket"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    except JWTError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    return user