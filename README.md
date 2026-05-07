## Integrantes
- Jacobo Rodriguez
- Jean Paul Cano
- José David Toro

## Link del video en el que se explica el proyecto:
https://youtu.be/zVQzvO4BpF4


# GroupsApp - Plataforma de Mensajería Distribuida

GroupsApp es una aplicación de chat en tiempo real basada en una arquitectura estricta de microservicios. Está diseñada para ser escalable, resiliente y mantener una separación clara de dominios, utilizando patrones modernos de comunicación síncrona y asíncrona.

## 🛠️ Stack Tecnológico

* **Frontend:** Next.js, React (Desacoplado)
* **API Gateway & Frameworks:** FastAPI, Python
* **Protocolos:** REST, WebSockets, gRPC, Protocol Buffers
* **Bases de Datos:** PostgreSQL (Multi-DB aislando dominios), SQLAlchemy
* **Mensajería Asíncrona:** RabbitMQ
* **Service Discovery:** HashiCorp Consul
* **Infraestructura:** Docker, Docker Compose, Kubernetes

---

## 🏗️ Arquitectura y Comunicación del Sistema

El sistema no opera como un monolito; está fragmentado en servicios especializados que se comunican a través de diferentes canales según la necesidad de rendimiento y acoplamiento:

### 1. El Punto de Entrada (API Gateway)
El **Gateway** es el único componente expuesto al exterior. El Frontend nunca habla directamente con los microservicios. 
* **Frontend -> Gateway (REST):** Las operaciones tradicionales (login, registro, crear grupos) se hacen mediante peticiones HTTP estándar.
* **Frontend -> Gateway (WebSockets):** La comunicación de chat en tiempo real mantiene una conexión bidireccional persistente por WS.

### 2. Comunicación Interna Síncrona (gRPC)
Cuando el Gateway necesita información de los microservicios (por ejemplo, validar un token de sesión o confirmar que un usuario pertenece a un grupo antes de enviarle un mensaje), utiliza **gRPC**. Al estar basado en HTTP/2 y transmitir datos binarios compilados (Protobuf), reduce la latencia interna casi a cero.
* Microservicios: `Auth` (Puerto 50051), `Groups` (Puerto 50052), `Presence` (Puerto 50053).

### 3. Service Discovery (Consul)
El sistema implementa enrutamiento dinámico. Las IPs de los contenedores de Auth, Groups y Presence no están "quemadas" (hardcoded) en el Gateway.
* Cada microservicio se **auto-registra** en Consul a través de su API HTTP al arrancar.
* Antes de que el Gateway o el Worker hagan una llamada gRPC, le preguntan a Consul: *"¿Cuál es la IP y puerto actual de este servicio?"*. Esto permite que los contenedores mueran, renazcan y escalen sin romper la comunicación.

### 4. Comunicación Asíncrona (RabbitMQ)
Para evitar bloquear el WebSocket durante procesos pesados (como generar registros de lectura para todos los miembros de un grupo grande), se utiliza una arquitectura orientada a eventos.
* El Gateway publica un evento de `nuevo_mensaje` en RabbitMQ.
* El **Messaging Worker** (consumidor) recibe el evento en segundo plano, consulta dinámicamente a `Groups` vía gRPC para obtener la lista de miembros, y guarda los recibos en la base de datos sin afectar la experiencia del usuario.

### 5. Aislamiento de Datos
Se respeta el principio de "Database per Service". Cada microservicio (Auth, Groups, Messages) tiene su propia base de datos aislada dentro de un clúster de PostgreSQL, previniendo el acoplamiento a nivel de datos.

---

## 📁 Estructura del Repositorio

```text
├── core/                   # Herramientas globales (DB, Consul Registry)
├── frontend/               # Aplicación Next.js cliente
├── modules/                # Lógica de Microservicios
│   ├── auth/               # gRPC Server & Router HTTP (Auth DB)
│   ├── consumers/          # Messaging Worker (RabbitMQ)
│   ├── groups/             # gRPC Server & Router HTTP (Groups DB)
│   ├── messaging/          # Routers WebSockets y Clientes gRPC
│   └── presence/           # gRPC Server (Memoria)
├── protos/                 # Contratos (auth.proto, groups.proto, presence.proto)
├── init-multiple-databases.sh # Script de inicialización PostgreSQL
├── main.py                 # API Gateway (FastAPI)
├── requirements.txt        # Dependencias de Python
└── docker-compose.yml      # Orquestación de infraestructura
```

---

## ⚙️ Configuración Inicial

Antes de levantar el proyecto, debes crear un archivo `.env` en la raíz del backend basándote en la siguiente plantilla:

```env
# Credenciales de la Base de Datos
DB_USER=admin
DB_PASSWORD=secretpassword

# Llaves de seguridad JWT
SECRET_KEY=tu_clave_super_secreta_jwt
```

*(El Frontend cuenta con su propia configuración automática hacia `localhost:8000` manejada por el `docker-compose.yml`).*

---

## 🐳 Ejecución con Docker Compose

La forma más rápida de probar todo el clúster es usando Docker Compose.

1. Clona el repositorio y compila los contratos Protobuf (si hubo cambios):
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/*.proto
   ```
2. Construye y levanta las imágenes en segundo plano:
   ```bash
   docker compose up --build -d
   ```
3. Verifica el estado de la infraestructura en tu navegador:
   * **Frontend App:** `http://localhost:3000`
   * **API Gateway Docs:** `http://localhost:8000/docs`
   * **Consul UI (Service Discovery):** `http://localhost:8500`
   * **RabbitMQ UI:** `http://localhost:15672` (usuario: `guest`, pass: `guest`)

Para detener el clúster y limpiar los volúmenes (reiniciar las bases de datos):
```bash
docker compose down -v
```

---

## 🚀 Despliegue en Entorno Local (Minikube)

Esta sección describe los pasos necesarios para desplegar la arquitectura completa de microservicios en un clúster local de Kubernetes.

### 1. Requisitos Previos
* **Minikube** iniciado y corriendo.
* **Docker** instalado.
* El clúster de Minikube debe tener suficiente memoria asignada (recomendado 4GB+).

### 2. Configuración del Entorno Docker
Para que Kubernetes pueda utilizar las imágenes construidas localmente sin necesidad de subirlas a un registro externo (como Docker Hub), se debe enlazar el cliente de Docker con el demonio interno de Minikube.

**Ejecutar en cada terminal nueva destinada a la construcción de imágenes:**
```bash
eval $(minikube docker-env)
```

### 3. Construcción de Imágenes
Desde la raíz del proyecto, construir las dos imágenes principales del sistema:

```bash
# Imagen Maestra del Backend (Python)
docker build -t groupsapp-backend:latest .

# Imagen del Frontend (Next.js)
docker build -t groupsapp-frontend:latest ./frontend
```

### 4. Orquestación y Despliegue
El despliegue se realiza aplicando los manifiestos de Kubernetes. Gracias al uso de **InitContainers**, el orden de inicio de los pods está orquestado de manera resiliente, asegurando que las bases de datos estén listas antes de que los servicios intenten conectarse.

```bash
# Aplicar todos los manifiestos
kubectl apply -f k8s/
```

### 5. Verificación de Salud
Es vital monitorear el clúster hasta que todos los componentes alcancen el estado `Running`.

```bash
kubectl get pods -w
```
> **Nota:** Los servicios pueden mostrar estados temporales como `Init:0/1` mientras esperan que la inicialización de PostgreSQL finalice. Esto es el comportamiento esperado.

### 6. Acceso a la Aplicación
Para acceder a los servicios desde el navegador de la máquina host, es necesario habilitar los puentes de red (túneles).

* **Túnel para el API Gateway (Backend):**
  Mantener esta terminal abierta para permitir el tráfico hacia la API.
  ```bash
  kubectl port-forward svc/api-gateway-service 8000:80
  ```

* **Acceso al Frontend:**
  Este comando abrirá automáticamente la interfaz web en el navegador.
  ```bash
  minikube service frontend-service
  ```

---

### 📝 Notas Técnicas del Despliegue
* **Aislamiento de Datos:** Se utiliza un **ConfigMap** (`00-init-db-config.yaml`) que inyecta un script de Bash para automatizar la creación de bases de datos independientes (`auth_db`, `groups_db`, `messages_db`) durante el primer arranque del clúster.
* **Resiliencia:** El API Gateway y los microservicios implementan **InitContainers** (`wait-for-postgres`) y **Probes (Liveness/Readiness)** para garantizar una inicialización robusta y recuperación automática ante fallos de red.
* **CORS:** El API Gateway está configurado para aceptar peticiones de origen cruzado desde `http://localhost:3000`.
