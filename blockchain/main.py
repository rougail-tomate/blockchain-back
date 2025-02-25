import dotenv
dotenv.load_dotenv()


from fastapi import FastAPI
from blockchain.routers import auth, psa
from blockchain.database import engine, Base


Base.metadata.create_all(bind=engine)

blockchain = FastAPI()

blockchain.include_router(auth.router)
blockchain.include_router(psa.router)
