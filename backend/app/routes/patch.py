from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.connection import get_db
from app.models.channel import Channel
import asyncio
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

router = APIRouter()

FFMPEG_EXE = os.getenv("FFMPEG_EXE", "ffmpeg")
LIVE_ROOT = Path(os.getenv("LIVE_ROOT", "./live_output")).resolve()
PLAYLIST_ROOT = LIVE_ROOT / "playlists"
HLS_ROOT = LIVE_ROOT / "hls"
HLS_TIME = int(os.getenv("HLS_TIME", "6"))
HLS_LIST_SIZE = int(os.getenv("HLS_LIST_SIZE", "10"))

PLAYLIST_ROOT.mkdir(parents=True, exist_ok=True)
HLS_ROOT.mkdir(parents=True, exist_ok=True)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal(self, websocket: WebSocket, data):
        await websocket.send_json(data)

    async def broadcast(self, data):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                dead_connections.append(connection)
        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()


class StreamWorker:
    def __init__(self, channel_name: str, channel_slug: str):
        self.channel_name = channel_name
        self.channel_slug = channel_slug
        self.proc: Optional[subprocess.Popen] = None
        self.signature: Optional[str] = None

    def output_dir(self) -> Path:
        out_dir = HLS_ROOT / self.channel_slug
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def playlist_path(self) -> Path:
        return PLAYLIST_ROOT / f"{self.channel_slug}.txt"

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=8)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.proc = None


STREAM_WORKERS: Dict[str, StreamWorker] = {}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "channel"


def get_obs_urls_for_channel(db: Session, channel_name: str) -> List[str]:
    sql = text("""
        SELECT COALESCE(NULLIF(http_url, ''), NULLIF(s3_url, '')) AS media_url
        FROM news_recordings
        WHERE channel_name = :channel_name
          AND COALESCE(NULLIF(http_url, ''), NULLIF(s3_url, '')) IS NOT NULL
        ORDER BY recorded_from ASC, id ASC
    """)
    rows = db.execute(sql, {"channel_name": channel_name}).fetchall()
    return [row.media_url for row in rows if row.media_url]


def write_concat_playlist(worker: StreamWorker, urls: List[str]) -> Path:
    playlist_path = worker.playlist_path()
    with open(playlist_path, "w", encoding="utf-8") as f:
        for url in urls:
            safe_url = url.replace("'", "'\\''")
            f.write(f"file '{safe_url}'\n")
    return playlist_path


def build_ffmpeg_command(worker: StreamWorker, playlist_path: Path) -> List[str]:
    out_dir = worker.output_dir()
    index_path = out_dir / "index.m3u8"
    segment_pattern = out_dir / "seg_%06d.ts"

    return [
        FFMPEG_EXE,
        "-hide_banner",
        "-loglevel", "warning",
        "-re",
        "-protocol_whitelist", "file,http,https,tcp,tls",
        "-f", "concat",
        "-safe", "0",
        "-i", str(playlist_path),
        "-fflags", "+genpts",
        "-vsync", "cfr",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "128k",
        "-f", "hls",
        "-hls_time", str(HLS_TIME),
        "-hls_list_size", str(HLS_LIST_SIZE),
        "-hls_flags", "delete_segments+append_list+omit_endlist+independent_segments",
        "-hls_segment_filename", str(segment_pattern),
        str(index_path),
    ]


def clear_hls_output(worker: StreamWorker):
    out_dir = worker.output_dir()
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)


def ensure_live_stream_for_channel(db: Session, channel_name: str) -> Optional[str]:
    urls = get_obs_urls_for_channel(db, channel_name)
    if not urls:
        return None

    channel_slug = slugify(channel_name)
    worker = STREAM_WORKERS.get(channel_slug)

    if worker is None:
        worker = StreamWorker(channel_name=channel_name, channel_slug=channel_slug)
        STREAM_WORKERS[channel_slug] = worker

    signature = f"{len(urls)}::{urls[-1]}"

    process_dead = worker.proc is None or worker.proc.poll() is not None
    playlist_changed = worker.signature != signature

    if process_dead or playlist_changed:
        worker.stop()
        clear_hls_output(worker)
        playlist_path = write_concat_playlist(worker, urls)
        cmd = build_ffmpeg_command(worker, playlist_path)
        worker.proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        worker.signature = signature

    return f"/live/hls/{channel_slug}/index.m3u8"


def fetch_live_channels(db: Session):
    channels = db.query(Channel).filter(Channel.is_enabled == True).all()
    response = []
    dirty = False

    for ch in channels:
        hls_url = ensure_live_stream_for_channel(db, ch.name)

        if getattr(ch, "channel_live_url", None) != hls_url:
            ch.channel_live_url = hls_url
            dirty = True

        response.append({
            "id": ch.id,
            "name": ch.name,
            "channel_live_url": ch.channel_live_url,
        })

    if dirty:
        db.commit()

    return response


@router.get("/live/channels")
def live_channels(db: Session = Depends(get_db)):
    return {"channels": fetch_live_channels(db)}


@router.get("/live/hls/{channel_slug}/{filename:path}")
def serve_hls_file(channel_slug: str, filename: str):
    base_dir = (HLS_ROOT / channel_slug).resolve()
    file_path = (base_dir / filename).resolve()

    if not str(file_path).startswith(str(base_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type = None
    if file_path.suffix == ".m3u8":
        media_type = "application/vnd.apple.mpegurl"
    elif file_path.suffix == ".ts":
        media_type = "video/mp2t"

    return FileResponse(path=file_path, media_type=media_type)


@router.websocket("/ws/live-channels")
async def websocket_live_channels(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            db_gen = get_db()
            db = next(db_gen)
            try:
                data = fetch_live_channels(db)
            finally:
                try:
                    db.close()
                except Exception:
                    pass

            await manager.send_personal(websocket, data)
            await asyncio.sleep(15)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)