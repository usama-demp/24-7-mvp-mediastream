import asyncio
import os

from app.routes import download
from fastapi import FastAPI
from app.database.connection import Base, engine
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth,users,channels,live,patch
from app.routes.newLive import router, live_data_publisher

app = FastAPI()
app.state.obs_endpoint = os.getenv("OBS_ENDPOINT", "http://192.168.2.11:9020")
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.213.1:3000",
    "http://172.16.1.7:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)

app.include_router(users.router)
app.include_router(channels.router)
# app.include_router(patch.router)
# app.include_router(live.router)
app.include_router(download.router)
app.include_router(router)
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(live_data_publisher())


# uvicorn app.main:app --reload command to run the server

# python -m venv venv command to install the virtual environment
# venv\Scripts\activate  command to activate the virtual environment
# pip install -r requirements.txt command to install the dependencies

#alembic revision --autogenerate -m "table_name table"
#alembic upgrade head