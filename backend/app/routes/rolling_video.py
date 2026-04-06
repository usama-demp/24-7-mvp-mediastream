import hashlib
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import boto3
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from sqlalchemy import text

from app.database.connection import get_db
from app.models.news_recording import NewsRecording
from app.models.channel import Channel

# Load combined env
load_dotenv(".env")

router = APIRouter()

# =========================
# Namespaced Rolling ENV
# =========================
OBS_ENDPOINT = os.getenv("ROLL_OBS_ENDPOINT")
OBS_BUCKET = os.getenv("ROLL_OBS_BUCKET")
OBS_ACCESS_KEY = os.getenv("ROLL_OBS_ACCESS_KEY")
OBS_SECRET_KEY = os.getenv("ROLL_OBS_SECRET_KEY")

FFMPEG = os.getenv("ROLL_FFMPEG_EXE", "ffmpeg")
CACHE_DIR = Path(os.getenv("ROLL_CHUNK_CACHE_DIR", "./chunk_cache")).resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MERGED_DIR = CACHE_DIR / "merged"
MERGED_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = CACHE_DIR / "_tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)

PLAY_GAP_SECONDS = int(os.getenv("ROLL_PLAY_GAP_SECONDS", "120"))
PLAYLIST_SIZE = int(os.getenv("ROLL_PLAYLIST_SIZE", "20"))
HOLD_BACK_SAFE_ROWS = int(os.getenv("ROLL_HOLD_BACK_SAFE_ROWS", "1"))
ROLLING_REFRESH_SECONDS = int(os.getenv("ROLL_ROLLING_REFRESH_SECONDS", "180"))
CHANNEL_NAME = os.getenv("ROLL_CHANNEL_NAME", "Sky News")

LOCK = threading.Lock()

# =========================
# Helper functions
# =========================
def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=OBS_ENDPOINT,
        aws_access_key_id=OBS_ACCESS_KEY,
        aws_secret_access_key=OBS_SECRET_KEY,
    )


def safe_name(text: str, suffix: str = ".mp4") -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest() + suffix


# def fetch_safe_rows(channel: str, db: Session, limit: int = 60) -> List[dict]:
#     safe_cutoff = datetime.now() - timedelta(seconds=PLAY_GAP_SECONDS)
#     print("incoming channel id: {}".format(channel))
#     # Step 1: Get channel ID by name
#     # channel = db.query(Channel).filter(Channel.name == channel).first()
#     # if not channel:
#     #     raise HTTPException(status_code=404, detail=f"Channel '{channel}' not found")
#     # channel_id = channel.id
#     # print(f"Fetching rows for channel_id={channel_id} with cutoff={safe_cutoff.isoformat()}")
#     channel_id = int(channel)
#     rows = (
#         db.query(NewsRecording.recorded_from, NewsRecording.recorded_to, NewsRecording.object_key)
#         .filter(NewsRecording.channel_id == channel)
#         .filter(NewsRecording.recorded_to <= safe_cutoff)
#         .order_by(NewsRecording.recorded_to.asc())
#         .limit(limit)
#         .all()
#     )
#     rows = [{"recorded_from": r.recorded_from, "recorded_to": r.recorded_to, "object_key": r.object_key} for r in rows]

#     if not rows:
#         return []

#     if HOLD_BACK_SAFE_ROWS > 0 and len(rows) > HOLD_BACK_SAFE_ROWS:
#         rows = rows[:-HOLD_BACK_SAFE_ROWS]

#     return rows[-PLAYLIST_SIZE:]



def fetch_safe_rows(channel: str, db: Session, limit: int = 60) -> List[dict]:
    """
    Fetch safe rows from the 'stream-backup' table for a given channel
    without needing an ORM model.
    """
    safe_cutoff = datetime.now() - timedelta(seconds=PLAY_GAP_SECONDS)
    print("Incoming channel name (test):", channel)

    # Quote the table name to handle hyphens
    sql = text("""
        SELECT recorded_from, recorded_to, object_key
        FROM "stream-backup"
        WHERE channel_name = :channel
          AND recorded_to <= :safe_cutoff
        ORDER BY recorded_to ASC
        LIMIT :limit
    """)

    result = db.execute(
        sql,
        {"channel": channel, "safe_cutoff": safe_cutoff, "limit": limit}
    ).all()

    # Convert rows to dicts
    rows = [
        {
            "recorded_from": r.recorded_from,
            "recorded_to": r.recorded_to,
            "object_key": r.object_key
        }
        for r in result
    ]

    # Apply hold-back logic
    if HOLD_BACK_SAFE_ROWS > 0 and len(rows) > HOLD_BACK_SAFE_ROWS:
        rows = rows[:-HOLD_BACK_SAFE_ROWS]

    # Return only the last PLAYLIST_SIZE rows
    return rows[-PLAYLIST_SIZE:]

def ensure_mp4_for_object_key(object_key: str) -> Path:
    s3 = get_s3()
    presigned = s3.generate_presigned_url(
        "get_object", Params={"Bucket": OBS_BUCKET, "Key": object_key}, ExpiresIn=3600
    )

    out_file = CACHE_DIR / safe_name(object_key)
    if out_file.exists() and out_file.stat().st_size > 0:
        return out_file

    tmp_out = TMP_DIR / (out_file.name + ".tmp.mp4")
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", presigned,
        "-map", "0:v:0?", "-map", "0:a:0?",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", "-avoid_negative_ts", "make_zero",
        str(tmp_out),
    ]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if cp.returncode != 0 or not tmp_out.exists() or tmp_out.stat().st_size == 0:
        raise HTTPException(status_code=500, detail=cp.stderr or f"Failed {object_key}")
    tmp_out.replace(out_file)
    return out_file


def build_concat_file(mp4_files: List[Path]) -> Path:
    concat_path = TMP_DIR / f"concat_{int(time.time()*1000)}.txt"
    concat_lines = ["file '{}'".format(str(p).replace("'", "'\\''")) for p in mp4_files]
    concat_path.write_text("\n".join(concat_lines), encoding="utf-8")
    return concat_path


def ensure_rolling_mp4(channel: str, db: Session) -> tuple[Path, List[dict]]:
    rows = fetch_safe_rows(channel, db=db, limit=max(PLAYLIST_SIZE + 20, 60))
    if not rows:
        raise HTTPException(status_code=404, detail="No safe rows found")

    merged_name = safe_name(channel + "|" + "|".join(r["object_key"] for r in rows), ".mp4")
    merged_path = MERGED_DIR / merged_name

    if merged_path.exists() and merged_path.stat().st_size > 0:
        return merged_path, rows

    with LOCK:
        mp4_files = []
        skipped_objects = []
        for r in rows:
            try:
                mp4_file = ensure_mp4_for_object_key(r["object_key"])
                mp4_files.append(mp4_file)
            except HTTPException as e:
                print(f"Skipping missing object {r['object_key']}: {e.detail}")
                skipped_objects.append(r["object_key"])

        if not mp4_files:
            raise HTTPException(status_code=404, detail="No valid video chunks found to merge")

        concat_file = build_concat_file(mp4_files)
        tmp_out = merged_path.parent / (merged_path.name + ".tmp.mp4")
        cmd = [
            FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", "-movflags", "+faststart", str(tmp_out)
        ]
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if cp.returncode != 0 or not tmp_out.exists() or tmp_out.stat().st_size == 0:
            print("FFMPEG merge failed:", cp.stderr)
            raise HTTPException(status_code=500, detail=cp.stderr or "merge failed")
        tmp_out.replace(merged_path)
        concat_file.unlink(missing_ok=True)

        if skipped_objects:
            print(f"Skipped {len(skipped_objects)} objects: {skipped_objects}")

    return merged_path, rows


# =========================
# API Endpoints
# =========================
@router.get("/api/status")
def api_status(channel: str = CHANNEL_NAME, db: Session = Depends(get_db)):
    rows = fetch_safe_rows(channel, db=db, limit=max(PLAYLIST_SIZE + 20, 60))
    return JSONResponse({
        "channel": channel,
        "count": len(rows),
        "first_recorded_to": str(rows[0]["recorded_to"]) if rows else None,
        "last_recorded_to": str(rows[-1]["recorded_to"]) if rows else None,
        "object_keys": [r["object_key"] for r in rows[-5:]] if rows else [],
    })

@router.get("/rolling.mp4")
def rolling_mp4(channel: str = CHANNEL_NAME, db: Session = Depends(get_db)):
    try:
        merged_path, _ = ensure_rolling_mp4(channel, db=db)
        return FileResponse(
            merged_path,
            media_type="video/mp4",
            filename=merged_path.name,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                     "Pragma": "no-cache",
                     "Expires": "0"},
        )
    except HTTPException as e:
        print("HTTPException:", e.detail)
        raise e
    except Exception as e:
        print("Unexpected error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))