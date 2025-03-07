from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas
from blockchain.models.user import User, PsaCert
import requests
import os
import json
from .xrpl import mint_token
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi import Security
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter()
PSA_ACCESS_TOKEN = os.environ.get("PSA_ACCESS_TOKEN")

if PSA_ACCESS_TOKEN is None:
    raise ValueError("PSA_ACCESS_TOKEN not found")

def get_current_user(token: str = Security(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"Token reçu: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/get-number/{cert_number}", response_model=schemas.PsaCertUniqueOut)
def get_psa_number_by_cert_number(cert_number: int, db: Session = Depends(get_db)):
    psa_cert = db.query(PsaCert).filter(PsaCert.cert_number == cert_number).first()

    if not psa_cert:
        raise HTTPException(status_code=404, detail="PSA number not found")

    return { "psaCerts": psa_cert }


@router.get("/users/get-numbers", response_model=schemas.PsaCertOut)
def get_psa_numbers_by_user_id(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    psa_certs = db.query(PsaCert).filter(PsaCert.user_id == current_user.id).all()
    return {"psaCerts": psa_certs}

@router.get("/get-all-numbers", response_model=schemas.PsaCertOut)
def get_all_psa_numbers(
    db: Session = Depends(get_db)
):
    psa_certs = db.query(PsaCert).all()

    if not psa_certs:
        raise HTTPException(status_code=404, detail="No PSA numbers found in the database")
    
    return {"psaCerts": psa_certs}

@router.post("/users/add-numbers", response_model=schemas.PsaCertBase)
def add_psa_number(
    number: schemas.PsaNumberCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cert_data = verify_psa_number(number.number)
    if not cert_data:
        raise HTTPException(status_code=400, detail="Invalid PSA number")

    if verify_psa_number_duplicate(number.number, db):
        raise HTTPException(status_code=400, detail="PSA number already exists")

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
        price=number.price,
        image=number.image,
        wallet=number.wallet
    )

    db.add(new_number)
    db.commit()
    db.refresh(new_number)

    res = mint_token(wallet=number.wallet, uri=f"http://localhost:8000/get-number/{number.number}") 
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