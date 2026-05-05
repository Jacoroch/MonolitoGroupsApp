from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_groups_db

from modules.groups import models, schemas
# Dependencia temporal permitida si el API Gateway sigue siendo el punto de entrada unificado
from modules.auth.router import get_current_user 

# ❌ ELIMINADO: from modules.auth.models import User

router = APIRouter(prefix="/groups", tags=["Grupos"])

@router.post("/", response_model=schemas.GroupResponse)
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_groups_db), 
    current_user = Depends(get_current_user) 
):
    new_group = models.Group(
        name=group.name,
        description=group.description,
        admin_id=current_user.id
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # ✅ CORREGIDO: Insertamos directamente en la tabla GroupMember
    new_member = models.GroupMember(group_id=new_group.id, user_id=current_user.id)
    db.add(new_member)
    db.commit()

    return new_group

# ❌ ELIMINADO: @router.get("/users/search") 
# (Este endpoint debes moverlo al router de Auth, modules/auth/router.py)

@router.post("/{group_id}/members")
def add_member_to_group(
    group_id: int, 
    member_data: schemas.MemberAdd,
    db: Session = Depends(get_groups_db),
    current_user = Depends(get_current_user)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    if group.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el administrador puede añadir miembros")
    
    # ✅ CORREGIDO: Validamos usando la tabla GroupMember
    miembros_actuales = [m.user_id for m in group.members]
    if member_data.user_id in miembros_actuales:
        raise HTTPException(status_code=400, detail="Este usuario ya es miembro del grupo")
    
    # Insertamos el nuevo miembro
    new_member = models.GroupMember(group_id=group.id, user_id=member_data.user_id)
    db.add(new_member)
    db.commit()
    
    return {"mensaje": f"Usuario con ID {member_data.user_id} añadido al grupo {group.name} con éxito"}

@router.get("/my-groups")
def get_my_groups(
    db: Session = Depends(get_groups_db),
    current_user = Depends(get_current_user)
):
    # ✅ CORREGIDO: Buscamos las membresías de este usuario específico
    mis_membresias = db.query(models.GroupMember).filter(models.GroupMember.user_id == current_user.id).all()
    
    return [
        {
            "id": membresia.group.id,
            "name": membresia.group.name
        }
        for membresia in mis_membresias
    ]

@router.get("/{group_id}/members")
def get_group_members(
    group_id: int,
    db: Session = Depends(get_groups_db),
    current_user = Depends(get_current_user)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    miembros_ids = [m.user_id for m in group.members]

    if current_user.id not in miembros_ids:
        raise HTTPException(status_code=403, detail="No perteneces a este grupo")

    # ✅ CORREGIDO: Como ya no tenemos la tabla User, solo podemos devolver IDs.
    # (El frontend o una llamada gRPC posterior deberá resolver los usernames)
    return {
        "members": [
            {
                "id": member.user_id,
                "is_admin": member.user_id == group.admin_id
            }
            for member in group.members
        ],
        "admin_id": group.admin_id,
        "current_user_id": current_user.id
    }

@router.delete("/{group_id}/members/{user_id}")
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_groups_db),
    current_user = Depends(get_current_user)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()

    if group.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo admin")

    # ✅ CORREGIDO: Buscamos el registro en GroupMember y lo borramos
    member_to_remove = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id, 
        models.GroupMember.user_id == user_id
    ).first()

    if not member_to_remove:
        raise HTTPException(status_code=404, detail="El usuario no está en el grupo")

    db.delete(member_to_remove)
    db.commit()

    return {"msg": "Usuario eliminado exitosamente"}