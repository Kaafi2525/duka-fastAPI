from datetime import datetime, timezone
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import get_db
from jsonmap import PurchaseGetMap, PurchasePostMap
from models import Purchase
from myjwt import get_current_user


router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get("", response_model=List[PurchaseGetMap])
def get_purchases(
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    purchases = select(Purchase)
    return db.scalars(purchases).all()


@router.post("", response_model=PurchaseGetMap)
def create_purchase(
    purchase: PurchasePostMap,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    new_purchase = Purchase(
        product_id=purchase.product_id,
        stock_quantity=purchase.stock_quantity,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return new_purchase


@router.put("/{purchase_id}", response_model=PurchaseGetMap)
def update_purchase(
    purchase_id: int,
    purchase: PurchasePostMap,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    db_purchase = db.get(Purchase, purchase_id)
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    db_purchase.product_id = purchase.product_id
    db_purchase.stock_quantity = purchase.stock_quantity
    db.commit()
    db.refresh(db_purchase)
    return db_purchase


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    db.delete(purchase)
    db.commit()
    return {"message": "Purchase deleted"}
