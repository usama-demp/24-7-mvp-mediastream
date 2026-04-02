from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.database.connection import Base
from sqlalchemy.orm import relationship

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    search_query = Column(String, nullable=True)
    channel_live_url = Column(String, nullable=True)

   
    allowed_terms = Column(JSON, nullable=True, default=[])
    blocked_terms = Column(JSON, nullable=True, default=[])

    is_enabled = Column(Boolean, default=True)

    recordings = relationship("NewsRecording", back_populates="channel")