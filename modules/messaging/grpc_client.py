import grpc
from fastapi import WebSocketException, status, HTTPException
import os

# --- IMPORTACIONES CORREGIDAS (Ambos contratos) ---
from protos import auth_pb2, auth_pb2_grpc
from protos import groups_pb2, groups_pb2_grpc

# ✅ IMPORTAMOS LA FUNCIÓN DE CONSUL
from core.consul_registry import get_service_url

# Mantenemos esto solo como "plan de respaldo" por si Consul se cae
FALLBACK_AUTH_URL = os.getenv('AUTH_SERVER_URL', 'auth-grpc-server:50051')
FALLBACK_GROUPS_URL = os.getenv('GROUPS_SERVER_URL', 'groups-grpc-server:50052')

def validate_token_ws(token: str):
    """Llama al microservicio de Auth por gRPC para validar un WebSocket"""
    
    # ✅ LE PREGUNTAMOS A CONSUL DÓNDE ESTÁ AUTH
    auth_url = get_service_url("auth-service", FALLBACK_AUTH_URL)
    print(f"\n📞 [CLIENTE gRPC] Iniciando llamada a {auth_url}...")
    
    try:
        with grpc.insecure_channel(auth_url) as channel:
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
    
    # ✅ LE PREGUNTAMOS A CONSUL DÓNDE ESTÁ AUTH
    auth_url = get_service_url("auth-service", FALLBACK_AUTH_URL)
    
    try:
        with grpc.insecure_channel(auth_url) as channel:
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
    
    # ✅ LE PREGUNTAMOS A CONSUL DÓNDE ESTÁ GROUPS
    groups_url = get_service_url("groups-service", FALLBACK_GROUPS_URL)
    print(f"📞 [CLIENTE gRPC] Preguntando a Grupos en {groups_url} si {user_id} está en {group_id}...")
    
    try:
        with grpc.insecure_channel(groups_url) as channel:
            stub = groups_pb2_grpc.GroupServiceStub(channel)
            request = groups_pb2.MembershipRequest(group_id=group_id, user_id=user_id)
            
            response = stub.CheckMembership(request)
            return response.is_member
    except grpc.RpcError as e:
        print(f"❌ [CLIENTE gRPC] Falla fatal conectando a Grupos: {e}")
        return False