import grpc
from concurrent import futures
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from protos import auth_pb2, auth_pb2_grpc
from core.database import SessionLocalAuth
from modules.auth import models
from modules.auth.router import SECRET_KEY, ALGORITHM # Importamos las llaves de tu router

class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    """
    Esta clase implementa las funciones que definimos en auth.proto
    """
    def ValidateToken(self, request, context):
        print(f"\n🛡️ [SERVIDOR gRPC] Petición recibida. Desencriptando token...")
        db = SessionLocalAuth()
        try:
            payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            print(f"🛡️ [SERVIDOR gRPC] Token descifrado. User ID: {user_id}")
            
            if user_id is None:
                print("❌ [SERVIDOR gRPC] El token no tiene 'sub'.")
                return auth_pb2.TokenResponse(is_valid=False)
            
            user = db.query(models.User).filter(models.User.id == int(user_id)).first()
            if user is None:
                print(f"❌ [SERVIDOR gRPC] El usuario con ID {user_id} no existe en la BD.")
                return auth_pb2.TokenResponse(is_valid=False)
            
            print(f"✅ [SERVIDOR gRPC] Usuario {user.username} autorizado exitosamente.")
            return auth_pb2.TokenResponse(
                is_valid=True, 
                user_id=user.id, 
                username=user.username
            )
        except JWTError as e:
            print(f"❌ [SERVIDOR gRPC] Token inválido o expirado: {e}")
            return auth_pb2.TokenResponse(is_valid=False)
        except Exception as e:
            print(f"❌ [SERVIDOR gRPC] Error interno inesperado: {e}")
            return auth_pb2.TokenResponse(is_valid=False)
        finally:
            db.close()

    def GetUser(self, request, context):
        db = SessionLocalAuth()
        try:
            user = db.query(models.User).filter(models.User.id == request.user_id).first()
            if user is None:
                # En gRPC, así se envían errores HTTP 404 (Not Found)
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details('Usuario no encontrado')
                return auth_pb2.UserResponse()
            
            return auth_pb2.UserResponse(
                user_id=user.id,
                username=user.username,
                email=user.email,
                is_active=True
            )
        finally:
            db.close()

def serve():
    # Creamos un servidor gRPC capaz de manejar 10 peticiones simultáneas
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Acoplamos nuestra clase AuthServicer al servidor
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    
    # Le decimos que escuche en el puerto 50051 (el puerto estándar de gRPC)
    server.add_insecure_port('[::]:50051')
    print("🚀 Servidor gRPC de Identidad corriendo en el puerto 50051...")
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()