import os
from typing import List, Optional

import boto3
from botocore.client import Config
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import channel, news_recording
from app.schemas.download import ChannelResponse, NewsRecordingResponse

router = APIRouter(prefix="/download", tags=["Download"])


def get_s3_client():
    endpoint = os.getenv("OBS_ENDPOINT")
    access_key = os.getenv("OBS_ACCESS_KEY")
    secret_key = os.getenv("OBS_SECRET_KEY")

    if not endpoint or not access_key or not secret_key:
        raise RuntimeError("OBS configuration is missing in environment variables")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
    )


def get_record_or_404(record_id: int, db: Session):
    record = (
        db.query(news_recording.NewsRecording)
        .filter(news_recording.NewsRecording.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Recording not found")
    return record


def get_duration_seconds(record) -> int:
    try:
        if record.recorded_from and record.recorded_to:
            diff = int((record.recorded_to - record.recorded_from).total_seconds())
            if diff > 0:
                return diff
    except Exception:
        pass
    return 600


@router.get("/channels", response_model=List[ChannelResponse])
def get_channels(db: Session = Depends(get_db)):
    return (
        db.query(channel.Channel)
        .filter(channel.Channel.is_enabled == True)
        .order_by(channel.Channel.id.asc())
        .all()
    )


@router.get("/recordings", response_model=List[NewsRecordingResponse])
def get_recordings(
    channel_id: Optional[int] = Query(None),
    start_datetime: Optional[str] = Query(None),
    end_datetime: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(news_recording.NewsRecording)

    if start_datetime:
        query = query.filter(news_recording.NewsRecording.created_at >= start_datetime)

    if end_datetime:
        query = query.filter(news_recording.NewsRecording.created_at <= end_datetime)

    if channel_id is not None:
        query = query.filter(news_recording.NewsRecording.channel_id == channel_id)

    records = (
        query.order_by(news_recording.NewsRecording.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []

    for r in records:
        response.append(
            NewsRecordingResponse(
                id=r.id,
                channel_id=r.channel_id,
                folder_name=r.folder_name,
                recorded_from=r.recorded_from,
                recorded_to=r.recorded_to,
                local_file_name=r.local_file_name,
                bucket_name=r.bucket_name,
                object_key=r.object_key,
                s3_url=r.s3_url,
                http_url=r.http_url,
                watch_url=r.watch_url,
                direct_url=None,
                file_size_bytes=r.file_size_bytes,
                upload_time=r.upload_time,
                created_at=r.created_at,
                video_url=f"/download/recordings/{r.id}/playlist.m3u8",
                download_url=f"/download/recordings/{r.id}/download",
            )
        )

    return response


@router.get("/recordings/{record_id}/playlist.m3u8")
def get_playlist(record_id: int, db: Session = Depends(get_db)):
    record = get_record_or_404(record_id, db)
    duration_seconds = get_duration_seconds(record)

    playlist = "\n".join(
        [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            "#EXT-X-PLAYLIST-TYPE:VOD",
            f"#EXT-X-TARGETDURATION:{max(1, round(duration_seconds))}",
            "#EXT-X-MEDIA-SEQUENCE:0",
            f"#EXTINF:{float(duration_seconds):.3f},",
            f"/download/recordings/{record_id}/segment.ts",
            "#EXT-X-ENDLIST",
            "",
        ]
    )

    return Response(
        content=playlist,
        media_type="application/vnd.apple.mpegurl",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        },
    )


@router.get("/recordings/{record_id}/segment.ts")
def stream_segment(record_id: int, db: Session = Depends(get_db)):
    record = get_record_or_404(record_id, db)

    try:
      s3 = get_s3_client()
      obj = s3.get_object(Bucket=record.bucket_name, Key=record.object_key)
    except Exception as e:
      raise HTTPException(status_code=502, detail=f"Failed to fetch OBS object: {str(e)}")

    body = obj["Body"]

    def iter_stream():
        try:
            while True:
                chunk = body.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    return StreamingResponse(
        iter_stream(),
        media_type="video/mp2t",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        },
    )


@router.get("/recordings/{record_id}/download")
def download_recording(record_id: int, db: Session = Depends(get_db)):
    record = get_record_or_404(record_id, db)

    try:
        s3 = get_s3_client()
        obj = s3.get_object(Bucket=record.bucket_name, Key=record.object_key)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch OBS object: {str(e)}")

    body = obj["Body"]
    filename = record.local_file_name or f"recording_{record.id}.ts"

    def iter_stream():
        try:
            while True:
                chunk = body.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    return StreamingResponse(
        iter_stream(),
        media_type="video/mp2t",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )