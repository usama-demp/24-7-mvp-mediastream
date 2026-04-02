from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from urllib.parse import quote

from app.database.connection import get_db
from app.models import news_recording, channel
from app.schemas.download import NewsRecordingResponse, ChannelResponse

router = APIRouter(prefix="/download", tags=["Download"])


def build_obs_object_url(bucket_name: str, object_key: str, request: Request) -> str:
    endpoint = request.app.state.obs_endpoint.rstrip("/")
    encoded_key = "/".join(quote(part) for part in object_key.split("/"))
    return f"{endpoint}/{bucket_name}/{encoded_key}"


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
    request: Request,
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
        obs_url = r.http_url or build_obs_object_url(r.bucket_name, r.object_key, request)

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
                direct_url=obs_url,
                file_size_bytes=r.file_size_bytes,
                upload_time=r.upload_time,
                created_at=r.created_at,
                video_url=obs_url,
                download_url=obs_url,
            )
        )

    return response