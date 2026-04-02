from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class ChannelCreate(BaseModel):
    name: str  # required
    search_query: Optional[str] = None
    channel_live_url: Optional[str] = None
    allowed_terms: Optional[List[str]] = None
    blocked_terms: Optional[List[str]] = None
    is_enabled: Optional[bool] = True

class ChannelResponse(ChannelCreate):
    id: int

    class Config:
        model_config = ConfigDict(from_attributes=True)