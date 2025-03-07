from pydantic import BaseModel
from typing import List, Optional
from pydantic_sqlalchemy  import sqlalchemy_to_pydantic
from blockchain.models.user import PsaCert, SellOrders

class PsaNumberCreate(BaseModel):
    number: int
    title: str
    description: str
    price : str
    image : str
    wallet: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    id_metamask: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    id_metamask: Optional[str] = None

    class Config:
        orm_mode = True

class UserAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserOut

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

class PsaCertUniqueOut(BaseModel):
    psaCerts: PsaCertBase

    class Config:
        orm_mode = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str