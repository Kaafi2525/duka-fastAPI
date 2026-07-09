# ===============================
# IMPORTS
# ===============================
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, field_validator
from pydantic_core import PydanticCustomError


# ===============================
# USER SCHEMAS
# ===============================
class UserPostRegister(BaseModel):
    fullname: str
    email: EmailStr
    password: str

    @field_validator("password")
    def password_length(cls, value):
        if len(value) < 6:
            raise PydanticCustomError(
                "password_too_short",
                "Password must be at least 6 characters long"
            )
        return value


class UserPostLogin(BaseModel):
    email: EmailStr
    password: str


# ===============================
# PRODUCT SCHEMAS
# ===============================
class ProductPostMap(BaseModel):
    name: str
    buying_price: float
    selling_price: float


class ProductGetMap(ProductPostMap):
    id: int

    class Config:
        from_attributes = True


# ===============================
# SALE SCHEMAS
# ===============================
class SalePostMap(BaseModel):
    product_id: int
    quantity: int


class SaleGetMap(SalePostMap):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===============================
# PURCHASE SCHEMAS
# ===============================
class PurchasePostMap(BaseModel):
    product_id: int
    stock_quantity: int


class PurchaseGetMap(BaseModel):
    id: int
    product_id: int
    stock_quantity: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===============================
# PAYMENT SCHEMAS
# ===============================
class PaymentPostMap(BaseModel):
    sale_id: Optional[int] = None
    phone_number: str
    trans_amount: float


class PaymentGetMap(BaseModel):
    id: int
    sale_id: Optional[int] = None
    mrid: Optional[str] = None
    crid: Optional[str] = None
    trans_code: Optional[str] = None
    trans_amount: Optional[float] = None
    phone_number: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===============================
# DASHBOARD SCHEMAS
# ===============================
class SalesPerProduct(BaseModel):
    data: List[int]
    labels: List[str]


class StockPerProduct(BaseModel):
    product_id: int
    product_name: str
    remaining_stock: int


# ===============================
# PROFIT SCHEMAS
# ===============================
class ProfitPerProduct(BaseModel):
    product_id: int
    product_name: str
    total_profit: float


class ProfitPerDay(BaseModel):
    date: datetime
    total_profit: float


class ProfitPerProductPerDay(BaseModel):
    date: datetime
    product_id: int
    product_name: str
    total_profit: float


# ===============================
# AUTH / TOKEN SCHEMAS
# ===============================
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[str] = None
    scopes: Optional[str] = None