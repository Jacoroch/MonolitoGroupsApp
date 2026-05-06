import os
import shutil
import grpc # <--- NUEVO: Importamos grpc
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status, HTTPException, File, UploadFile, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
from typing import List
from uuid import uuid4
from core.database import get_messaging_db
from modules.messaging.sockets import ConnectionManager
from modules.messaging import models as msg_models
from modules.messaging import schemas as msg_schemas
from modules.messaging.rabbitmq_client import publish_new_message_event

# Importamos las herramientas gRPC
from modules.messaging.grpc_client import validate_token_ws, validate_token_http, check_membership_grpc

# <--- NUEVO: Importamos los protos de Presencia
import protos.presence_pb2 as presence_pb2
import protos.presence_pb2_grpc as presence_pb2_grpc

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_grpc(token: str = Depends(oauth2_scheme)):
    """Middleware que usa gRPC para validar las peticiones HTTP normales"""
    return validate_token_http(token)


router = APIRouter(prefix="/ws", tags=["Mensajería en Tiempo Real"])
manager = ConnectionManager()

# <--- NUEVO: Helper para notificar presencia sin bloquear el chat
def notify_presence(user_id: int, status: str):
    try:
        presence_url = os.getenv("PRESENCE_SERVER_URL", "presence-grpc-server:50053")
        with grpc.insecure_channel(presence_url) as channel:
            stub = presence_pb2_grpc.PresenceServiceStub(channel)
            # Convertimos el user_id a string porque así lo definimos en el .proto
            stub.UpdateStatus(presence_pb2.StatusUpdateRequest(
                user_id=str(user_id),
                status=status
            ))
    except Exception as e:
        print(f"[WARNING] No se pudo actualizar presencia para el usuario {user_id}: {e}")


@router.websocket("/groups/{group_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    group_id: int,
    token: str = Query(...),
    db: Session = Depends(get_messaging_db)
):
    # 1. Autorización de Identidad por gRPC
    current_user = validate_token_ws(token)

    # 2. Autorización de Grupos por gRPC
    is_member = check_membership_grpc(group_id=group_id, user_id=current_user["id"])

    if not is_member:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, group_id)
    
    # <--- NUEVO: Avisamos al servicio de presencia que el usuario entró al chat
    notify_presence(current_user["id"], "online")

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "send_message")

            if action == "send_message":
                content = data.get("content")
                media_url = data.get("media_url") 
                
                if not content and not media_url:
                    continue

                # Guardamos el mensaje
                new_message = msg_models.Message(
                    content=content,
                    media_url=media_url, 
                    sender_id=current_user["id"], 
                    group_id=group_id
                )
                db.add(new_message)
                db.commit() 
                db.refresh(new_message)
                
                # Lanzamos el evento a RabbitMQ
                publish_new_message_event(
                    group_id=group_id, 
                    message_id=new_message.id, 
                    sender_id=current_user["id"]
                )

                message_payload = {
                    "action": "new_message",
                    "message_id": new_message.id,
                    "sender_id": current_user["id"], 
                    "sender_username": current_user["username"], 
                    "content": new_message.content,
                    "media_url": new_message.media_url, 
                    "created_at": new_message.created_at.isoformat()
                }
                
                await manager.broadcast_to_group(group_id, message_payload)

            elif action == "mark_read":
                message_id = data.get("message_id")
                if not message_id:
                    continue

                receipt = db.query(msg_models.MessageReceipt).filter(
                    msg_models.MessageReceipt.message_id == message_id,
                    msg_models.MessageReceipt.user_id == current_user["id"] 
                ).first()

                if receipt and not receipt.read_at:
                    receipt.read_at = datetime.utcnow()
                    db.commit()

                    read_payload = {
                        "action": "receipt_updated",
                        "message_id": message_id,
                        "user_id": current_user["id"], 
                        "status": "read",
                        "timestamp": receipt.read_at.isoformat()
                    }
                    await manager.broadcast_to_group(group_id, read_payload)

    except WebSocketDisconnect:
        manager.disconnect(websocket, group_id)
        # <--- NUEVO: Avisamos al servicio de presencia que el usuario salió
        notify_presence(current_user["id"], "offline")


@router.get("/groups/{group_id}/messages", response_model=List[msg_schemas.MessageResponse])
def get_group_message_history(
    group_id: int,
    limit: int = 50,
    db: Session = Depends(get_messaging_db),
    current_user: dict = Depends(get_current_user_grpc) 
):
    # Validamos vía gRPC en lugar de usar db.query(Group)
    is_member = check_membership_grpc(group_id=group_id, user_id=current_user["id"])
    
    if not is_member:
        raise HTTPException(status_code=403, detail="No tienes acceso al historial de este grupo")

    messages = (
        db.query(msg_models.Message)
        .filter(msg_models.Message.group_id == group_id)
        .options(selectinload(msg_models.Message.receipts))
        .order_by(msg_models.Message.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return messages

# --- Envio de archivos ---
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

@router.post("/messages/upload")
async def upload_media(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_grpc) 
):
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    media_url = f"/static/{unique_filename}"

    return {
        "mensaje": "Archivo subido exitosamente",
        "media_url": media_url,
        "filename": unique_filename
    }

@router.post("/groups/{group_id}/messages")
def send_message_http(
    group_id: int,
    message: msg_schemas.MessageCreate, 
    db: Session = Depends(get_messaging_db),
    current_user: dict = Depends(get_current_user_grpc) 
):
    # Validamos vía gRPC
    is_member = check_membership_grpc(group_id=group_id, user_id=current_user["id"])
    
    if not is_member:
        raise HTTPException(status_code=403, detail="No perteneces a este grupo")

    new_message = msg_models.Message(
        content=message.content,
        media_url=message.media_url,
        sender_id=current_user["id"], 
        group_id=group_id
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "id": new_message.id,
        "content": new_message.content,
        "media_url": new_message.media_url,
        "created_at": new_message.created_at,
        "sender_id": current_user["id"], 
        "sender_username": current_user["username"] 
    }
    
    # --- Consulta de Presencia ---
@router.get("/users/{user_id}/status")
def get_user_presence(user_id: int, current_user: dict = Depends(get_current_user_grpc)):
    """Endpoint para que el frontend consulte si un usuario está online"""
    try:
        presence_url = os.getenv("PRESENCE_SERVER_URL", "presence-grpc-server:50053")
        with grpc.insecure_channel(presence_url) as channel:
            stub = presence_pb2_grpc.PresenceServiceStub(channel)
            response = stub.GetUserStatus(presence_pb2.GetStatusRequest(user_id=str(user_id)))
            
            return {
                "user_id": response.user_id,
                "status": response.status,
                "last_updated": response.last_updated
            }
    except Exception as e:
        # Si el servicio de presencia falla, por defecto decimos que está offline
        return {"user_id": str(user_id), "status": "offline", "last_updated": "N/A"}

