import grpc
from concurrent import futures
from sqlalchemy.orm import Session

from protos import groups_pb2, groups_pb2_grpc
# ✅ CORREGIDO: Importamos la sesión específica de grupos a nivel global
from core.database import SessionLocalGroups
from modules.groups import models

# ✅ IMPORTACIÓN DE CONSUL
from core.consul_registry import register_to_consul

class GroupServicer(groups_pb2_grpc.GroupServiceServicer):
    def CheckMembership(self, request, context):
        print(f"\n📁 [SERVIDOR GRUPOS] Verificando usuario {request.user_id} en grupo {request.group_id}...")
        
        # ✅ CORREGIDO: Usamos la nueva sesión
        db = SessionLocalGroups()
        
        try:
            group = db.query(models.Group).filter(models.Group.id == request.group_id).first()
            if not group:
                print("❌ [SERVIDOR GRUPOS] El grupo no existe.")
                return groups_pb2.MembershipResponse(is_member=False)
            
            is_member = any(member.user_id == request.user_id for member in group.members)
            print(f"✅ [SERVIDOR GRUPOS] ¿Es miembro? {is_member}")
            
            return groups_pb2.MembershipResponse(is_member=is_member)
        finally:
            db.close()
    
    def GetGroupMembers(self, request, context):
        print(f"\n📁 [SERVIDOR GRUPOS] Solicitud de miembros para el grupo {request.group_id}...")
        
        # ✅ CORREGIDO: Usamos la sesión global, ya no necesitamos importarla aquí adentro
        db = SessionLocalGroups()
        
        try:
            membresias = db.query(models.GroupMember).filter(models.GroupMember.group_id == request.group_id).all()
            
            user_ids = [m.user_id for m in membresias]
            print(f"✅ [SERVIDOR GRUPOS] Devolviendo {len(user_ids)} miembros.")
            
            return groups_pb2.GroupMembersResponse(user_ids=user_ids)
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    groups_pb2_grpc.add_GroupServiceServicer_to_server(GroupServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("📁 Servidor gRPC de Directorio de Grupos corriendo en el puerto 50052...")
    
    server.start()
    
    # ✅ REGISTRO EN CONSUL
    register_to_consul("groups-service", "groups-grpc-server", 50052)
    
    server.wait_for_termination()

if __name__ == '__main__':
    serve()