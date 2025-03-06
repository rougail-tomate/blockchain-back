from pydantic import BaseModel
from typing import List
from pydantic_sqlalchemy  import sqlalchemy_to_pydantic
from blockchain.models.user import PsaCert
class PsaNumberCreate(BaseModel):
    number: int
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
    id_metamask: str

    class Config:
        orm_mode = True


PsaCertBase = sqlalchemy_to_pydantic(PsaCert, exclude=["id"])

class PsaCertOut(BaseModel):
    psaCerts: List[PsaCertBase]

    class Config:
        orm_mode = True