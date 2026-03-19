import os
import shutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status, HTTPException, File, UploadFile
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
from uuid import uuid4

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
            
            # --- MULTIPLEXACIÓN DE EVENTOS ---
            action = data.get("action", "send_message") # Si no envía "action", asume que es un mensaje nuevo

            # EVENTO A: Creación de un nuevo mensaje
            if action == "send_message":
                content = data.get("content")
                media_url = data.get("media_url") 
                
                # Validación básica del payload
                if not content and not media_url:
                    continue

                # Transacción principal: Guardar el mensaje
                new_message = msg_models.Message(
                    content=content,
                    media_url=media_url, 
                    sender_id=current_user.id,
                    group_id=group_id
                )
                db.add(new_message)
                db.flush() # Flush asigna el ID a 'new_message' sin cerrar la transacción en base de datos

                # Transacción secundaria: Generar los recibos pendientes para los demás miembros del grupo
                for member in group.members:
                    if member.id != current_user.id:
                        receipt = msg_models.MessageReceipt(
                            message_id=new_message.id,
                            user_id=member.id,
                            delivered_at=datetime.utcnow() 
                        )
                        db.add(receipt)

                db.commit() # Confirmamos mensaje y recibos atómicamente
                db.refresh(new_message)

                # Broadcast: Construimos el DTO (Data Transfer Object) de salida
                message_payload = {
                    "action": "new_message",
                    "message_id": new_message.id,
                    "sender_id": current_user.id,
                    "sender_username": current_user.username,
                    "content": new_message.content,
                    "media_url": new_message.media_url, 
                    "created_at": new_message.created_at.isoformat()
                }
                
                await manager.broadcast_to_group(group_id, message_payload)

            # EVENTO B: Actualización de estado a "Leído"
            elif action == "mark_read":
                message_id = data.get("message_id")
                if not message_id:
                    continue

                # Buscar el recibo correspondiente a este usuario y este mensaje en la base de datos
                receipt = db.query(msg_models.MessageReceipt).filter(
                    msg_models.MessageReceipt.message_id == message_id,
                    msg_models.MessageReceipt.user_id == current_user.id
                ).first()

                # Si existe y no ha sido leído aún, actualizamos el timestamp
                if receipt and not receipt.read_at:
                    receipt.read_at = datetime.utcnow()
                    db.commit()

                    # Emitir un evento de actualización al grupo
                    read_payload = {
                        "action": "receipt_updated",
                        "message_id": message_id,
                        "user_id": current_user.id,
                        "status": "read",
                        "timestamp": receipt.read_at.isoformat()
                    }
                    await manager.broadcast_to_group(group_id, read_payload)

    except WebSocketDisconnect:
        # 6. Limpieza: Liberamos los recursos en memoria al perder el socket
        manager.disconnect(websocket, group_id)


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

# --- Envio de archivos ---
# Ruta absoluta al directorio de uploads que acabamos de crear
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

@router.post("/messages/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user) # Autenticación HTTP estándar
):
    # 1. Generar un nombre de archivo único para evitar colisiones (ej. si dos usuarios suben "foto.jpg")
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 2. Escribir el archivo en el disco duro del servidor
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Construir la URL relativa que se guardará en la base de datos
    media_url = f"/static/{unique_filename}"

    return {
        "mensaje": "Archivo subido exitosamente",
        "media_url": media_url,
        "filename": unique_filename
    }