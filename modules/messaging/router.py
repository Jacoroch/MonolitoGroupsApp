from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from core.database import get_db
from modules.messaging.sockets import ConnectionManager
from modules.messaging import models as msg_models
from modules.groups.models import Group
from modules.auth.models import User
from modules.auth.router import get_current_user_ws
from modules.auth.router import get_current_user # Autenticación HTTP estándar
from modules.messaging import schemas as msg_schemas

router = APIRouter(prefix="/ws", tags=["Mensajería en Tiempo Real"])

# Instanciamos el manejador de conexiones para este enrutador
manager = ConnectionManager()

@router.websocket("/groups/{group_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_ws)
):
    # 1. Autorización: Verificamos la existencia del grupo y la membresía del usuario
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group or current_user not in group.members:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 2. Handshake: Aceptamos la conexión y la registramos en memoria
    await manager.connect(websocket, group_id)

    try:
        while True:
            # 3. Recepción: Esperamos un payload en formato JSON
            data = await websocket.receive_json()
            content = data.get("content")
            
            # Validación básica del payload
            if not content:
                continue

            # 4. Persistencia: Transacción síncrona a PostgreSQL
            new_message = msg_models.Message(
                content=content,
                sender_id=current_user.id,
                group_id=group_id
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            # 5. Broadcast: Construimos el DTO (Data Transfer Object) de salida
            message_payload = {
                "message_id": new_message.id,
                "sender_id": current_user.id,
                "sender_username": current_user.username,
                "content": new_message.content,
                "created_at": new_message.created_at.isoformat()
            }
            
            # Transmitimos el mensaje a todos los descriptores de archivo del grupo
            await manager.broadcast_to_group(group_id, message_payload)

    except WebSocketDisconnect:
        # 6. Limpieza: Liberamos los recursos en memoria al perder el socket
        manager.disconnect(websocket, group_id)
        # Opcional: Emitir evento de desconexión del sistema
        # await manager.broadcast_to_group(group_id, {"system": f"Usuario {current_user.username} desconectado."})

@router.get("/groups/{group_id}/messages", response_model=List[msg_schemas.MessageResponse])
def get_group_message_history(
    group_id: int,
    limit: int = 50, # Paginación por defecto: últimos 50 mensajes
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Autorización: Verificar que el grupo exista y el usuario sea miembro
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    
    if current_user not in group.members:
        raise HTTPException(status_code=403, detail="No tienes acceso al historial de este grupo")

    # 2. Consulta ORM: Obtener mensajes ordenados por fecha descendente (más recientes primero)
    messages = (
        db.query(msg_models.Message)
        .filter(msg_models.Message.group_id == group_id)
        .order_by(msg_models.Message.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return messages