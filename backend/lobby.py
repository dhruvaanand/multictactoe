from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
import json
from backend.database import mongo_db

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, uid: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[uid] = websocket

    def disconnect(self, uid: str):
        if uid in self.active_connections:
            del self.active_connections[uid]

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/lobby/{uid}")
async def lobby_websocket(websocket: WebSocket, uid: str, request: Request):
    await manager.connect(uid, websocket)
    
    mysql_pool = websocket.app.state.mysql
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET is_online = TRUE WHERE uid = %s", (uid,))
        await conn.commit()

    await manager.broadcast({"type": "player_update", "uid": uid, "status": "online"})

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "invite":
                target_uid = message.get("target")
                if target_uid in manager.active_connections:
                    await manager.active_connections[target_uid].send_json({
                        "type": "invite_received",
                        "from": uid
                    })

    except WebSocketDisconnect:
        manager.disconnect(uid)
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET is_online = FALSE WHERE uid = %s", (uid,))
            await conn.commit()
        await manager.broadcast({"type": "player_update", "uid": uid, "status": "offline"})

@router.get("/lobby/players")
async def get_players(request: Request):
    mysql_pool = request.app.state.mysql
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT uid, name, elo_rating, is_online FROM users")
            result = await cur.fetchall()
            
    players = []
    for row in result:
        players.append({
            "uid": row[0],
            "name": row[1],
            "elo": row[2],
            "status": "ONLINE" if row[3] else "OFFLINE"
        })
    return players
