import os
import requests

CONSUL_HOST = os.getenv("CONSUL_HOST", "consul-server")
CONSUL_PORT = os.getenv("CONSUL_PORT", "8500")

def register_to_consul(service_name: str, service_host: str, service_port: int):
    """Registra el microservicio en el directorio de Consul"""
    url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/agent/service/register"
    
    payload = {
        "ID": f"{service_name}-{service_port}",
        "Name": service_name,
        "Address": service_host,
        "Port": service_port,
        "Check": {
            # Consul revisará cada 10 segundos que el puerto gRPC siga abierto
            "TCP": f"{service_host}:{service_port}",
            "Interval": "10s",
            "Timeout": "2s"
        }
    }
    
    try:
        response = requests.put(url, json=payload)
        if response.status_code == 200:
            print(f"✅ {service_name} registrado en Consul exitosamente en {service_host}:{service_port}")
        else:
            print(f"❌ Fallo al registrar {service_name}: {response.text}")
    except Exception as e:
        print(f"❌ Error conectando a Consul: {e}")

def get_service_url(service_name: str, fallback_url: str):
    """Pregunta a Consul dónde está el servicio. Si falla, usa el fallback."""
    url = f"http://{CONSUL_HOST}:{CONSUL_PORT}/v1/catalog/service/{service_name}"
    try:
        response = requests.get(url, timeout=2)
        data = response.json()
        if data and len(data) > 0:
            # Tomamos la primera instancia disponible que nos devuelva Consul
            address = data[0]["ServiceAddress"]
            port = data[0]["ServicePort"]
            return f"{address}:{port}"
    except Exception as e:
        print(f"⚠️ Consul no respondió para {service_name}, usando fallback...")
    
    return fallback_url