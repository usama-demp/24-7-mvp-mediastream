# app/routes/users.py
from app.models import user
from app.schemas import user
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from passlib.context import CryptContext
router = APIRouter(prefix="/users", tags=["Users"])


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Hash the password before storing it
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    db_user = User(**user_dict)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "user").all()

@router.get("/{id}", response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(404, "User not found")

    return user

@router.put("/{id}", response_model=UserResponse)
def update_user(id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(404, "User not found")

    # Update basic info
    db_user.username = user.username
    db_user.email = user.email

    # Update password only if provided
    if user.password:
        db_user.password = pwd_context.hash(user.password)

    db.commit()
    db.refresh(db_user)

    return db_user

@router.delete("/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()

    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()

    return {"message": "Deleted"}