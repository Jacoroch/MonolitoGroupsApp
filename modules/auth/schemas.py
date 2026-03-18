from pydantic import BaseModel

# Molde de entrada: Lo que esperamos recibir del Frontend
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Molde de salida: Lo que le respondemos al Frontend
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        # Esto permite que Pydantic lea la información directamente desde nuestro modelo de base de datos
        from_attributes = True