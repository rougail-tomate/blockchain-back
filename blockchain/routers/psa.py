from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas
from blockchain.models.user import User, PsaCert
from blockchain.schemas import SellOrder, MarketPlaceCardView, MarketPlaceView, PsaCertBase
from blockchain.models.user import SellOrders
from blockchain.routers.user import get_current_user
import requests
import os
import json
from .xrpl import mint_token, add_sell_order 
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import Security
from datetime import datetime, timedelta
from typing import List

HOST = os.environ.get('HOST_ORIGIN')

router = APIRouter()
PSA_ACCESS_TOKEN = os.environ.get("PSA_ACCESS_TOKEN")

if PSA_ACCESS_TOKEN is None:
    raise ValueError("PSA_ACCESS_TOKEN not found")

def _get_marketplace_order_if_exists(cert_number: int, db: Session):
    res = db.query(SellOrders).filter(SellOrders.nft_id == cert_number).first()
    return SellOrder(
        cert_number=cert_number,
        user_id=-1,
        taker_pay=res.taker_pays,
        destination=res.destination,
        sell_hash=res.sell_hash,
    ) if res else None

def _match_all_marketplace_orders_matching_certs(certs, db: Session):
    return [MarketPlaceCardView(psa_cert=cert, sell_order=_get_marketplace_order_if_exists(cert.cert_number, db)) for cert in certs]

@router.get("/get-number/{cert_number}", response_model=schemas.MarketPlaceCardView)
def get_psa_number_by_cert_number(cert_number: int, db: Session = Depends(get_db)):
    psa_cert = db.query(PsaCert).filter(PsaCert.cert_number == cert_number).first()
    if not psa_cert:
        raise HTTPException(status_code=404, detail="PSA number not found")
    return MarketPlaceCardView(psa_cert=psa_cert, sell_order=_get_marketplace_order_if_exists(psa_cert.cert_number, db))

@router.get("/users/get-numbers", response_model=schemas.MarketPlaceView)
def get_psa_numbers_by_user_id(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    psa_certs = db.query(PsaCert).filter(PsaCert.user_id == current_user.id).all()
    return MarketPlaceView(market_place=_match_all_marketplace_orders_matching_certs(psa_certs, db))

@router.get("/get-all-numbers", response_model=schemas.MarketPlaceView)
def get_all_psa_numbers(db: Session = Depends(get_db)):
    psa_certs = db.query(PsaCert).all()
    return MarketPlaceView(market_place=_match_all_marketplace_orders_matching_certs(psa_certs, db))

@router.get("/view-marketplace", response_model=schemas.MarketPlaceView)
def get_marketplace(db: Session = Depends(get_db)):
    #return MarketPlaceView(market_place=list(filter(lambda x: x.sell_order is not None, _match_all_marketplace_orders_matching_certs(db.query(PsaCert).all(), db))))
    return MarketPlaceView(market_place=_match_all_marketplace_orders_matching_certs(db.query(PsaCert).all(), db))

@router.post("/users/add-numbers", response_model=schemas.PsaCertBase)
def add_psa_number(
    number: schemas.PsaNumberCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # print(number)
    cert_data = verify_psa_number(number.number)
    if not cert_data:
        raise HTTPException(status_code=400, detail="Invalid PSA number")

    if verify_psa_number_duplicate(number.number, db):
        raise HTTPException(status_code=400, detail="PSA number already exists")

    res = mint_token(wallet=number.wallet, uri=f"{HOST}/get-number/{number.number}")

    print('TOKEN ID = ', res['meta']['nftoken_id'])
    new_number = PsaCert(
        cert_number=number.number,
        spec_id=cert_data["PSACert"]["SpecID"],
        spec_number=cert_data["PSACert"]["SpecNumber"],
        label_type=cert_data["PSACert"]["LabelType"],
        reverse_bar_code=cert_data["PSACert"]["ReverseBarCode"],
        brand=cert_data["PSACert"]["Brand"],
        category=cert_data["PSACert"]["Category"],
        subject=cert_data["PSACert"]["Subject"],
        card_grade=cert_data["PSACert"]["CardGrade"],
        user_id=current_user.id,
        title=number.title,
        description=number.description,
        #price=number.price,
        image=number.image,
        wallet=number.wallet,
        nftoken_id=res['meta']['nftoken_id']
    )

    # if (number.is_selling is True):
    # print(res)
    db.add(new_number)
    db.commit()
    db.refresh(new_number)

    print(res)

    return new_number

def verify_psa_number(number):
    url = f"https://api.psacard.com/publicapi/cert/GetByCertNumber/{str(number).zfill(8)}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"bearer {PSA_ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    print(url, response.status_code, response.text)
    if response.status_code != 200:
        return None
    try:
        if response.text == "Invalid certificate number":
            return None
        cert_data = json.loads(response.text)
        return cert_data
    except json.JSONDecodeError:
        return None

def verify_psa_number_duplicate(number, db):
    existing_number = db.query(PsaCert).filter(PsaCert.cert_number == number).first()
    if existing_number:
        return True
    return False