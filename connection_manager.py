from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except:
            pass

    async def close(self):
        for websocket in self.active_connections:
            await websocket.close()
        self.active_connections = []

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except:
                self.disconnect(websocket)
