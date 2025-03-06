from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas
from blockchain.models.user import User, PsaCert
import requests
import os
import json

router = APIRouter()
PSA_ACCESS_TOKEN = os.environ.get("PSA_ACCESS_TOKEN")
if PSA_ACCESS_TOKEN is None:
    raise ValueError("PSA_ACCESS_TOKEN not found")


@router.get("/users/{user_id}/numbers", response_model=schemas.PsaCertOut)
def get_psa_numbers_by_user_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    psa_certs = db.query(PsaCert).filter(PsaCert.user_id == user_id).all()
    return {"psaCerts": psa_certs}

@router.post("/users/{user_id}/numbers", response_model=schemas.PsaCertBase)
def add_psa_number(user_id: int, number: schemas.PsaNumberCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
        year=cert_data["PSACert"]["Year"],
        brand=cert_data["PSACert"]["Brand"],
        category=cert_data["PSACert"]["Category"],
        card_number=cert_data["PSACert"]["CardNumber"],
        subject=cert_data["PSACert"]["Subject"],
        variety=cert_data["PSACert"]["Variety"],
        is_psadna=cert_data["PSACert"]["IsPSADNA"],
        is_dual_cert=cert_data["PSACert"]["IsDualCert"],
        grade_description=cert_data["PSACert"]["GradeDescription"],
        card_grade=cert_data["PSACert"]["CardGrade"],
        total_population=cert_data["PSACert"]["TotalPopulation"],
        total_population_with_qualifier=cert_data["PSACert"]["TotalPopulationWithQualifier"],
        population_higher=cert_data["PSACert"]["PopulationHigher"],
        user_id=user_id
    )

    db.add(new_number)
    db.commit()
    db.refresh(new_number)

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