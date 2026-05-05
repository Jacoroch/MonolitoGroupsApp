import grpc
from concurrent import futures
from sqlalchemy.orm import Session
from modules.auth.models import User

# Importamos los contratos de grupos
from protos import groups_pb2, groups_pb2_grpc

# Conexión a BD y modelos de grupos
from core.database import SessionLocal
from modules.groups import models

class GroupServicer(groups_pb2_grpc.GroupServiceServicer):
    def CheckMembership(self, request, context):
        print(f"\n📁 [SERVIDOR GRUPOS] Verificando usuario {request.user_id} en grupo {request.group_id}...")
        db = SessionLocal()
        try:
            # Buscamos el grupo
            group = db.query(models.Group).filter(models.Group.id == request.group_id).first()
            if not group:
                print("❌ [SERVIDOR GRUPOS] El grupo no existe.")
                return groups_pb2.MembershipResponse(is_member=False)
            
            # Verificamos si el usuario es miembro
            is_member = any(member.id == request.user_id for member in group.members)
            print(f"✅ [SERVIDOR GRUPOS] ¿Es miembro? {is_member}")
            
            return groups_pb2.MembershipResponse(is_member=is_member)
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    groups_pb2_grpc.add_GroupServiceServicer_to_server(GroupServicer(), server)
    
    # ¡OJO! Puerto 50052 para Grupos
    server.add_insecure_port('[::]:50052')
    print("📁 Servidor gRPC de Directorio de Grupos corriendo en el puerto 50052...")
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()