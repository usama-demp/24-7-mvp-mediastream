from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional


class NewsRecordAltResponse(BaseModel):
    id: int
    channel_name: Optional[str] = None
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

    play_url: Optional[str] = None
    download_url: Optional[str] = None

    class Config:
        model_config = ConfigDict(from_attributes=True)


class ChannelNameResponse(BaseModel):
    channel_name: str