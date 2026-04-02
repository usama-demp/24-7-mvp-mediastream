from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import asyncio

from app.database.connection import get_db, SessionLocal
from app.models.channel import Channel
from app.newYoutube import get_live_video_embed  # now async

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.last_payload = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"❌ Client disconnected: {len(self.active_connections)}")

    async def broadcast(self, data):
        dead_connections = []
        for conn in self.active_connections:
            try:
                await conn.send_json(data)
            except Exception:
                dead_connections.append(conn)
        for conn in dead_connections:
            self.disconnect(conn)


manager = ConnectionManager()


async def fetch_live_channels(db: Session):
    channels = db.query(Channel).all()
    result = []

    for ch in channels:
        try:
            live_url = await get_live_video_embed(ch.name)
        except Exception as e:
            print(f"[yt-dlp error] {ch.name}: {e}")
            live_url = None

        result.append({
            "id": ch.id,
            "name": ch.name,
            "channel_live_url": live_url
        })

    return result


async def live_data_publisher():
    while True:
        db = SessionLocal()
        try:
            data = await fetch_live_channels(db)
            if data != manager.last_payload:
                manager.last_payload = data
                await manager.broadcast(data)
        except Exception as e:
            print("🔥 Publisher error:", e)
        finally:
            db.close()

        await asyncio.sleep(5)  # refresh interval


@router.websocket("/ws/new-live-channels")
async def websocket_live_channels(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        if manager.last_payload:
            await websocket.send_json(manager.last_payload)
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print("❌ WebSocket error:", e)
        manager.disconnect(websocket)