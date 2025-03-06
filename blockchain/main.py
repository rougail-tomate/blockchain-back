import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI
from blockchain.routers import auth, psa
from blockchain.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

blockchain = FastAPI()

origins = [
    "http://localhost:3000",
]

blockchain.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

blockchain.include_router(auth.router)
blockchain.include_router(psa.router)
