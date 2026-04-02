from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional


class NewsRecordingBase(BaseModel):
    channel_id: int
    folder_name: str
    recorded_from: datetime
    recorded_to: datetime
    local_file_name: str
    bucket_name: str
    object_key: str
    s3_url: str
    http_url: Optional[str] = None
    watch_url: Optional[str] = None
    direct_url: Optional[str] = None
    file_size_bytes: Optional[int] = None


class NewsRecordingCreate(NewsRecordingBase):
    pass


class NewsRecordingResponse(BaseModel):
    id: int
    channel_id: Optional[int] = None
    folder_name: Optional[str] = None
    recorded_from: Optional[datetime] = None
    recorded_to: Optional[datetime] = None
    local_file_name: Optional[str] = None
    bucket_name: Optional[str] = None
    object_key: Optional[str] = None
    s3_url: Optional[str] = None
    http_url: Optional[str] = None
    watch_url: Optional[str] = None
    direct_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    upload_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    video_url: Optional[str] = None
    download_url: Optional[str] = None
    poster_url: Optional[str] = None

    class Config:
        model_config = ConfigDict(from_attributes=True)