from pydantic import BaseModel,ConfigDict
from datetime import datetime
from typing import Optional


class ChannelResponse(BaseModel):
    id: int
    name: str

    class Config:
        model_config = ConfigDict(from_attributes=True)

class NewsRecordingResponse(BaseModel):
    id: int
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
    upload_time: datetime
    created_at: datetime
    video_url: str
    download_url: str

    class Config:
       model_config = ConfigDict(from_attributes=True)