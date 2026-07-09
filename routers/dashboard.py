from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import get_db
from jsonmap import SalesPerProduct
from models import Product, Sale
from myjwt import get_current_user


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/spp", response_model=List[SalesPerProduct])
def sales_per_product(
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(get_current_user),
):
    results = db.execute(
        select(
            Sale.product_id,
            Product.name,
            func.sum(Sale.quantity),
        )
        .join(Product)
        .group_by(Sale.product_id, Product.name)
    ).all()

    data = [result[2] for result in results]
    labels = [result[1] for result in results]
    return [SalesPerProduct(data=data, labels=labels)]
