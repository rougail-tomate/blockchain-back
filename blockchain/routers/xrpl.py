from xrpl.clients import JsonRpcClient

from xrpl.models.requests import AccountNFTs
from xrpl.models.transactions import NFTokenCreateOffer, NFTokenAcceptOffer, NFTokenMint
from xrpl.transaction import sign_and_submit, submit_and_wait 
from xrpl.wallet import generate_faucet_wallet, Wallet


from ..database import get_db

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from blockchain.models.user import User, PsaCert, SellOrders

from .. import schemas

XRPL_RPC_URL = "https://s.altnet.rippletest.net:51234"
client = JsonRpcClient(XRPL_RPC_URL)
wallet1 = Wallet.from_seed("sEd7CWyK17UAD2VwC8LdAqbDWS896eF")

router = APIRouter()

@router.get("/nfts")
def get_nfts(userid: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    nfts = AccountNFTs(account=user.wallet)
    return client.request(nfts).result

@router.post("/sell")
def add_sell_order(sell_order: schemas.SellOrders, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == sell_order.seller_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    nft = db.query(PsaCert).filter(PsaCert.id == sell_order.nft_id).first()
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    if sell_order.destination is None:
        sell_offer = NFTokenCreateOffer(
            account=user.wallet,
            taker_gets=nft.id, taker_pays=str(sell_order.taker_pays),
            amount=str(sell_order.taker_pays), flags=1
        )
    else:
        sell_offer = NFTokenCreateOffer(
            account=user.wallet,
            taker_gets=nft.id, taker_pays=str(sell_order.taker_pays),
            amount=str(sell_order.taker_pays), destination=sell_order.destination,
            flags=1
        )
    response = client.request(sell_offer)
    if response.is_successful():
        sell_order.sell_hash = response.result["hash"]
        db.add(sell_order)
        db.commit()
        db.refresh(sell_order)
        return sell_order
    else:
        return response.result

def mint_token(wallet: str, uri: str):

    mint_tx = NFTokenMint(
        account=wallet1.address,
        uri=uri.encode("utf-8").hex(),
        flags=8, # Transferable NFT
        transfer_fee=1, # 0.01%
        nftoken_taxon=0
    )
    print("Mint ", mint_tx.to_dict())
    print("Wallet info ", wallet1.address, wallet1)
    response = submit_and_wait(mint_tx, client, wallet1)
    print("Response ", response)
    return response.result

'''
@router.post("/buy")
def buy_order(buy_order: schemas.BuyOrder, db: Session = Depends(get_db)):
    sell_order = db.query(SellOrders).filter(SellOrders.sell_hash == buy_order.sell_hash).first()

    if not sell_order:
        raise HTTPException(status_code=404, detail="Sell order not found")

    buy_offer = NFTokenAcceptOffer(
        account=buy_order.wallet, offer_sequence=sell_order.sell_hash
    )

    response = sign_and_submit(buy_offer, buy_order.wallet)
    if response.is_successful():
        db.query(SellOrders).filter(SellOrders.nft_id == sell_order.nft_id).delete()
        db.commit()
    return response.result
'''