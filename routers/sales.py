from datetime import datetime, timezone
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db import get_db
from jsonmap import SaleGetMap, SalePostMap
from models import Sale
from myjwt import get_current_user


router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=List[SaleGetMap])
def get_sales(
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    sales = select(Sale).options(selectinload(Sale.product))
    return db.scalars(sales).all()


@router.post("", response_model=SaleGetMap)
def create_sale(
    sale: SalePostMap,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    new_sale = Sale(
        product_id=sale.product_id,
        quantity=sale.quantity,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale


@router.put("/{sale_id}", response_model=SaleGetMap)
def update_sale(
    sale_id: int,
    sale: SalePostMap,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    db_sale = db.get(Sale, sale_id)
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    db_sale.product_id = sale.product_id
    db_sale.quantity = sale.quantity
    db.commit()
    db.refresh(db_sale)
    return db_sale


@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    db.delete(sale)
    db.commit()
    return {"message": "Sale deleted"}
