from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.user import User
from app.core.security import verify_password, create_token
from app.schemas.auth import LoginRequest  # <-- import the model

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password):
        return {"error": "Invalid credentials"}

    token = create_token({"sub": user.username, "role": user.role})

    return {"access_token": token,"role":user.role}