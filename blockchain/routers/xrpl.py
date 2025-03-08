from xrpl.clients import JsonRpcClient

from xrpl.models.requests import AccountNFTs
from xrpl.models.transactions import NFTokenCreateOffer, NFTokenAcceptOffer, NFTokenMint
from xrpl.transaction import sign_and_submit, submit_and_wait 
from xrpl.wallet import generate_faucet_wallet, Wallet
from blockchain.models.user import User, PsaCert

from ..database import get_db

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from blockchain.models.user import User, PsaCert, SellOrders

from .. import schemas
from blockchain.routers.user import get_current_user

XRPL_RPC_URL = "https://s.altnet.rippletest.net:51234"
# client = JsonRpcClient(XRPL_RPC_URL)
#  replace this by using the wallet of the user
# wallet1 = Wallet.from_seed("sEd7CWyK17UAD2VwC8LdAqbDWS896eF")

router = APIRouter()

@router.get("/nfts")
def get_nfts(userBody: schemas.RetrieveNfts, db: Session = Depends(get_db)):
    client = JsonRpcClient(XRPL_RPC_URL)
    user = db.query(User).filter(User.id == userBody.user_id).first()
    user_wallet = Wallet.from_seed(userBody.wallet)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    nfts = AccountNFTs(account=user_wallet.address)
    return client.request(nfts).result

@router.post("/sell")
def add_sell_order_route(sell_order: schemas.SellOrder, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    add_sell_order(sell_order, db, current_user)

def add_sell_order(sell_order: schemas.SellOrder, db, current_user):
    client = JsonRpcClient(XRPL_RPC_URL)
    print("SELL ORDER = ", sell_order)
    user_wallet = Wallet.from_seed(current_user.id_metamask)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    nft = db.query(PsaCert).filter(PsaCert.cert_number == sell_order.cert_number).first()
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")
    sell_offer = NFTokenCreateOffer(
        account=user_wallet.address,
        nftoken_id=nft.nftoken_id,
        amount=str(sell_order.taker_pay * 1000000), destination=None,
        flags=1
    )
    response = submit_and_wait(sell_offer, client, user_wallet)
    if response.is_successful():
        order = SellOrders(
            nft_id=sell_order.cert_number,
            taker_pays=sell_order.taker_pay,
            destination=sell_order.destination,
            sell_hash=""
        )
        order.sell_hash = response.result["meta"]["offer_id"]
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    else:
        return response.r

def buy_order(pbuy_order: schemas.BuyOrder, db, current_user):
    client = JsonRpcClient(XRPL_RPC_URL)
    sell_order = db.query(SellOrders).filter(SellOrders.sell_hash == pbuy_order.sell_hash).first()
    user_wallet = Wallet.from_seed(current_user.id_metamask)

    if not sell_order:
        raise HTTPException(status_code=404, detail="Sell order not found")

    buy_offer = NFTokenAcceptOffer(
        account=user_wallet.address,
        nftoken_sell_offer=sell_order.sell_hash
    )

    response = submit_and_wait(buy_offer, client, user_wallet)
    if response.is_successful():
        db.query(SellOrders).filter(SellOrders.nft_id == sell_order.nft_id).delete()
        nft = db.query(PsaCert).filter(PsaCert.cert_number == sell_order.nft_id).first()
        nft.wallet = user_wallet.address
        nft.user_id = current_user.id
        db.commit()
        db.refresh(nft)
    return response.result

@router.post("/buy")
def buy_order_route(pbuy_order: schemas.BuyOrder, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return buy_order(pbuy_order, db, current_user)

def mint_token(wallet: str, uri: str):
    client = JsonRpcClient(XRPL_RPC_URL)
    print("wallet = ", wallet)
    user_wallet = Wallet.from_seed(wallet)
    print("wallet address = ", user_wallet.address)
    mint_tx = NFTokenMint(
        account=user_wallet.address,
        uri=uri.encode("utf-8").hex(),
        flags=8, # Transferable NFT
        transfer_fee=1, # 0.01%
        nftoken_taxon=0
    )
    print("Mint ", mint_tx.to_dict())
    print("Wallet info ", user_wallet.address, user_wallet)
    response = submit_and_wait(mint_tx, client, user_wallet)
    print("Response ", response)
    return response.result

def get_nft_data(wallet_owner, uri):
    client = JsonRpcClient(XRPL_RPC_URL)
    user_wallet = Wallet.from_seed(wallet_owner)
    print("wallet address = ", user_wallet.address)
    # print("user id in account = ", userBody.wallet)
    nfts = AccountNFTs(account=user_wallet.address)
    return client.request(nfts).result

@router.get('/orders')
def get_order(db: Session = Depends(get_db)):
    order = db.query(SellOrders).all()
    return order

@router.get("/order/{nft_id}")
def get_order_by_nft_id(nft_id: int, db: Session = Depends(get_db)):
    order = db.query(SellOrders).filter(SellOrders.nft_id == nft_id).first()
    return order