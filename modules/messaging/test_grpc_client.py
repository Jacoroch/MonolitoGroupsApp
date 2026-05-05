import grpc

# Importamos los contratos generados
from protos import auth_pb2, auth_pb2_grpc

def run_test():
    print("📞 Iniciando cliente gRPC de Mensajería...")
    
    # 1. Abrir el canal de comunicación hacia el puerto de Auth
    with grpc.insecure_channel('localhost:50051') as channel:
        
        # 2. Instanciar el "Stub" (el objeto que hace el trabajo pesado de red)
        stub = auth_pb2_grpc.AuthServiceStub(channel)
        
        # 3. Crear el mensaje usando el DTO estricto definido en el .proto
        # Vamos a enviar un token falso a propósito para ver cómo responde
        request = auth_pb2.TokenRequest(token="eyUnTokenFalsoParaLaPrueba12345")
        
        print("➡️ Enviando TokenRequest al servicio de Auth...")
        
        # 4. ¡HACER LA LLAMADA DE RED!
        response = stub.ValidateToken(request)
        
        # 5. Imprimir la respuesta binaria que fue decodificada automáticamente a Python
        print("\n✅ ¡Respuesta recibida del Microservicio de Identidad!")
        print("--------------------------------------------------")
        print(f"¿Token Válido? : {response.is_valid}")
        print(f"ID del Usuario : {response.user_id}")
        print(f"Nombre Usuario : {response.username}")
        print("--------------------------------------------------")

if __name__ == '__main__':
    run_test()