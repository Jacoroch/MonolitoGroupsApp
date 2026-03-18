from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db

from modules.groups import models, schemas
from modules.auth.router import get_current_user
from modules.auth.models import User

from fastapi import HTTPException

router = APIRouter(prefix="/groups", tags=["Grupos"])

# Fíjate cómo inyectamos "current_user". ¡Si no hay token, la petición rebota aquí!
@router.post("/", response_model=schemas.GroupResponse)
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user) # <- ¡El guardia de seguridad!
):
    # 1. Creamos el grupo asignando al usuario actual como administrador
    new_group = models.Group(
        name=group.name,
        description=group.description,
        admin_id=current_user.id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # 2. Truco de magia de SQLAlchemy: Añadimos al creador a la tabla intermedia de miembros
    new_group.members.append(current_user)
    db.commit()

    return new_group

@router.post("/{group_id}/members")
def add_member_to_group(
    group_id: int, 
    member_data: schemas.MemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Buscamos el grupo en la base de datos
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    # 2. Regla de negocio: ¿El que hace la petición es el administrador?
    if group.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el administrador puede añadir miembros")
    
    # 3. Buscamos al usuario que queremos añadir (Carlos o María)
    user_to_add = db.query(User).filter(User.id == member_data.user_id).first()
    if not user_to_add:
        raise HTTPException(status_code=404, detail="El usuario que intentas añadir no existe")
    
    # 4. Verificamos que no esté ya en el grupo para no duplicar datos
    if user_to_add in group.members:
        raise HTTPException(status_code=400, detail="Este usuario ya es miembro del grupo")
    
    # 5. Magia de SQLAlchemy: Lo añadimos a la lista y guardamos
    group.members.append(user_to_add)
    db.commit()
    
    return {"mensaje": f"Usuario {user_to_add.username} añadido al grupo {group.name} con éxito"}