from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models import news_recording

scheduler = BackgroundScheduler()

def delete_old_records():
    """Delete records older than 2 days from news_recordings table."""
    cutoff_time = datetime.utcnow() - timedelta(days=2)
    db: Session = next(get_db())
    try:
        deleted_count = db.query(news_recording.NewsRecording)\
            .filter(news_recording.NewsRecording.recorded_to < cutoff_time)\
            .delete(synchronize_session=False)
        db.commit()
        print(f"[{datetime.utcnow()}] Deleted {deleted_count} old records older than {cutoff_time}")
    except Exception as e:
        db.rollback()
        print(f"[{datetime.utcnow()}] Error deleting records: {e}")
    finally:
        db.close()

# Run daily at 2 AM
scheduler.add_job(delete_old_records, 'cron', hour=2, minute=0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting scheduler...")
    scheduler.start()
    yield
    print("Shutting down scheduler...")
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)