from sqlalchemy.orm import Session
from app.database.connection import SessionLocal, Base, engine
from app.models.user import User
from faker import Faker
from passlib.context import CryptContext

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Initialize Faker for random users
fake = Faker()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Number of random users
NUM_USERS = 3

def seed_admin():
    db: Session = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists!")
            return

        admin_password = pwd_context.hash("admin123")
        admin = User(
            username="admin",
            email="admin@example.com",
            password=admin_password,
            role="admin"  # Change to "media_manager" if needed
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
    except Exception as e:
        db.rollback()
        print("Error creating admin:", e)
    finally:
        db.close()


def seed_random_users():
    db: Session = SessionLocal()
    try:
        for _ in range(NUM_USERS):
            username = fake.user_name()
            email = fake.unique.email()
            password = pwd_context.hash("user123")
            role = "user"

            # Skip if email already exists
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                continue

            user = User(
                username=username,
                email=email,
                password=password,
                role=role
            )
            db.add(user)
        db.commit()
        print(f"{NUM_USERS} random users inserted successfully!")
    except Exception as e:
        db.rollback()
        print("Error seeding users:", e)
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
    seed_random_users()