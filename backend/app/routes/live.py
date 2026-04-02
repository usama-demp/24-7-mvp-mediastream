# app/routes/live_channels.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.channel import Channel
from app.youtube import get_channel_id_by_name, get_live_video_url
import asyncio

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                # Ignore failed sends
                pass

manager = ConnectionManager()

# Function to fetch live channels and update URLs if changed
async def fetch_live_channels(db: Session):
    channels = db.query(Channel).filter(Channel.is_enabled == True).all()
    response = []

    for ch in channels:
        live_url = None

        # Dynamically get YouTube ID
        youtube_id = get_channel_id_by_name(ch.name)
        if youtube_id:
            live_url = get_live_video_url(youtube_id)
        print(f"Fetched live URL for {ch.name}: {live_url}")
        # Save the URL if it is currently null
        if ch.channel_live_url is None and live_url:
            ch.channel_live_url = live_url
            db.commit()
            db.refresh(ch)

        # Optionally, you can also update if URL changes
        elif ch.channel_live_url != live_url:
            ch.channel_live_url = live_url
            db.commit()
            db.refresh(ch)
        print(f"Final URL for {ch.name}: {ch.channel_live_url}")
        response.append({
            "id": ch.id,
            "name": ch.name,
            "channel_live_url": ch.channel_live_url,  # now saved in DB
        })

    return response
# WebSocket endpoint
@router.websocket("/ws/live-channels")
async def websocket_live_channels(websocket: WebSocket, db: Session = Depends(get_db)):
    # Allow all origins (or limit to frontend origins if needed)
    await manager.connect(websocket)
    try:
        while True:
            data = await fetch_live_channels(db)
            await manager.broadcast(data)
            await asyncio.sleep(15)  # Refresh every 15 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
