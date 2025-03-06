from pydantic import BaseModel
from typing import List
from pydantic_sqlalchemy  import sqlalchemy_to_pydantic
from blockchain.models.user import PsaCert, SellOrders

class PsaNumberCreate(BaseModel):
    number: int
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True


PsaCertBase = sqlalchemy_to_pydantic(PsaCert, exclude=["id"])
SellOrders = sqlalchemy_to_pydantic(SellOrders, exclude=["id", "sell_hash"])

class BuyOrder:
    wallet: str
    sell_hash: str

class PsaCertOut(BaseModel):
    psaCerts: List[PsaCertBase]

    class Config:
        orm_mode = True