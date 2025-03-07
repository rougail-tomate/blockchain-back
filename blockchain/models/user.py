from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    id_metamask = Column(String, nullable=False)

class PsaCert(Base):
    __tablename__ = "psa_certs"

    id = Column(Integer, primary_key=True, index=True)
    cert_number = Column(Integer, nullable=False)
    spec_id = Column(Integer, nullable=False)
    spec_number = Column(String, nullable=False)
    label_type = Column(String, nullable=False)
    reverse_bar_code = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    card_grade = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(String, nullable=False)
    image = Column(String, nullable=False)
    wallet = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class SellOrders(Base):
    __tablename__ = "sell_orders"

    id = Column(Integer, primary_key=True, index=True)
    nft_id = Column(Integer, ForeignKey("psa_certs.id"), nullable=False)
    taker_pays = Column(Integer, nullable=False)
    destination = Column(String, nullable=True)
    sell_hash = Column(String, nullable=False, index=True)
