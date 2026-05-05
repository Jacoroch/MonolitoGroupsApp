import grpc
from fastapi import WebSocketException, status, HTTPException
import os

# --- IMPORTACIONES CORREGIDAS (Ambos contratos) ---
from protos import auth_pb2, auth_pb2_grpc
from protos import groups_pb2, groups_pb2_grpc

# --- URLs DE TUS SERVIDORES ---
AUTH_SERVER_URL = os.getenv('AUTH_SERVER_URL', 'localhost:50051')
GROUPS_SERVER_URL = os.getenv('GROUPS_SERVER_URL', 'localhost:50052')

def validate_token_ws(token: str):
    """Llama al microservicio de Auth por gRPC para validar un WebSocket"""
    print(f"\n📞 [CLIENTE gRPC] Iniciando llamada a {AUTH_SERVER_URL}...")
    try:
        with grpc.insecure_channel(AUTH_SERVER_URL) as channel:
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            request = auth_pb2.TokenRequest(token=token)
            
            print("📞 [CLIENTE gRPC] Enviando TokenRequest...")
            response = stub.ValidateToken(request)
            print(f"📞 [CLIENTE gRPC] Respuesta recibida: is_valid={response.is_valid}, user_id={response.user_id}")
            
            if not response.is_valid:
                print("❌ [CLIENTE gRPC] El servidor de Auth rechazó el token.")
                raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
            
            return {
                "id": response.user_id,
                "username": response.username
            }
    except grpc.RpcError as e:
        print(f"❌ [CLIENTE gRPC] Falla fatal de conexión de red: {e}")
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR)

def validate_token_http(token: str):
    """Llama al microservicio de Auth por gRPC para rutas HTTP (ej. historial)"""
    try:
        with grpc.insecure_channel(AUTH_SERVER_URL) as channel:
            stub = auth_pb2_grpc.AuthServiceStub(channel)
            request = auth_pb2.TokenRequest(token=token)
            
            response = stub.ValidateToken(request)
            
            if not response.is_valid:
                raise HTTPException(status_code=401, detail="Token inválido o expirado")
            
            return {
                "id": response.user_id,
                "username": response.username
            }
    except grpc.RpcError:
        raise HTTPException(status_code=503, detail="Servicio de autenticación no disponible")

def check_membership_grpc(group_id: int, user_id: int) -> bool:
    """Pregunta al microservicio de Grupos si un usuario pertenece a un grupo"""
    print(f"📞 [CLIENTE gRPC] Preguntando a Grupos (Puerto 50052) si {user_id} está en {group_id}...")
    try:
        with grpc.insecure_channel(GROUPS_SERVER_URL) as channel:
            stub = groups_pb2_grpc.GroupServiceStub(channel)
            request = groups_pb2.MembershipRequest(group_id=group_id, user_id=user_id)
            
            response = stub.CheckMembership(request)
            return response.is_member
    except grpc.RpcError as e:
        print(f"❌ [CLIENTE gRPC] Falla fatal conectando a Grupos: {e}")
        return False