from fastapi import FastAPI
from blockchain.routers import auth
from blockchain.database import engine, Base

Base.metadata.create_all(bind=engine)

blockchain = FastAPI()

blockchain.include_router(auth.router)
