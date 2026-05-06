import grpc
from concurrent import futures
import time
from datetime import datetime

# Importamos los archivos generados por protoc
import protos.presence_pb2 as presence_pb2
import protos.presence_pb2_grpc as presence_pb2_grpc

# Base de datos en memoria (Diccionario)
# Estructura: {"1": {"status": "online", "last_updated": "2026-05-06 15:30:00"}}
presence_db = {}

class PresenceServiceServicer(presence_pb2_grpc.PresenceServiceServicer):
    
    def UpdateStatus(self, request, context):
        user_id = request.user_id
        status = request.status
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Guardamos en nuestra "base de datos"
        presence_db[user_id] = {
            "status": status,
            "last_updated": now
        }
        
        print(f"[PRESENCIA] Usuario {user_id} ahora está {status.upper()}")
        
        return presence_pb2.StatusResponse(
            user_id=user_id,
            status=status,
            last_updated=now
        )

    def GetUserStatus(self, request, context):
        user_id = request.user_id
        
        # Buscamos al usuario, si no existe, por defecto está offline
        user_data = presence_db.get(user_id, {"status": "offline", "last_updated": "N/A"})
        
        return presence_pb2.StatusResponse(
            user_id=user_id,
            status=user_data["status"],
            last_updated=user_data["last_updated"]
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    presence_pb2_grpc.add_PresenceServiceServicer_to_server(PresenceServiceServicer(), server)
    
    # Lo levantaremos en el puerto 50053
    server.add_insecure_port('[::]:50053')
    print("Servicio de Presencia gRPC iniciado en el puerto 50053...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()