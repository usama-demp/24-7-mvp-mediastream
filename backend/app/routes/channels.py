# app/routes/channels.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelResponse

router = APIRouter(prefix="/channels", tags=["Channels"])

@router.post("/", response_model=ChannelResponse)
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    db_channel = Channel(**channel.dict(exclude_unset=True))
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

@router.get("/", response_model=list[ChannelResponse])
def get_channels(db: Session = Depends(get_db)):
    return db.query(Channel).all()

@router.put("/{id}", response_model=ChannelResponse)
def update_channel(id: int, channel: ChannelCreate, db: Session = Depends(get_db)):
    db_channel = db.query(Channel).filter(Channel.id == id).first()
    if not db_channel:
        raise HTTPException(404, "Channel not found")

    for field, value in channel.dict(exclude_unset=True).items():
        setattr(db_channel, field, value)

    db.commit()
    db.refresh(db_channel)
    return db_channel

@router.delete("/{id}")
def delete_channel(id: int, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter(Channel.id == id).first()

    if not channel:
        raise HTTPException(404, "Channel not found")

    db.delete(channel)
    db.commit()

    return {"message": "Deleted"}