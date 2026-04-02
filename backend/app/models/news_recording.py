from sqlalchemy import Column, BigInteger, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class NewsRecording(Base):
    __tablename__ = "news_recordings"

    id = Column(BigInteger, primary_key=True, index=True)

    # 🔥 Foreign key to channels table
    channel_id = Column(BigInteger, ForeignKey("channels.id"), nullable=False)

    folder_name = Column(Text, nullable=False)

    recorded_from = Column(TIMESTAMP, nullable=False)
    recorded_to = Column(TIMESTAMP, nullable=False)

    local_file_name = Column(Text, nullable=False)

    bucket_name = Column(Text, nullable=False)
    object_key = Column(Text, nullable=False)

    s3_url = Column(Text, nullable=False)
    http_url = Column(Text, nullable=True)
    watch_url = Column(Text, nullable=True)
    direct_url = Column(Text, nullable=True)

    file_size_bytes = Column(BigInteger, nullable=True)

    upload_time = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # 🔥 Relationship
    channel = relationship("Channel", back_populates="recordings")