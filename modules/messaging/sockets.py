from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Diccionario para mapear: group_id -> lista de WebSockets activos
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group_id: int):
        await websocket.accept()
        if group_id not in self.active_connections:
            self.active_connections[group_id] = []
        self.active_connections[group_id].append(websocket)

    def disconnect(self, websocket: WebSocket, group_id: int):
        if group_id in self.active_connections:
            self.active_connections[group_id].remove(websocket)
            # Limpieza de memoria si el grupo queda vacío
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]

    async def broadcast_to_group(self, group_id: int, message: dict):
        """Transmite un payload JSON a todos los sockets activos de un grupo específico."""
        if group_id in self.active_connections:
            for connection in self.active_connections[group_id]:
                await connection.send_json(message)

# Instancia global del gestor (Singleton en el contexto del proceso actual)
manager = ConnectionManager()