from typing import List, Optional
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'fastapi_usersp'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    fullname: Mapped[Optional[str]] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(255), nullable=False)


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    buying_price: Mapped[float] = mapped_column(Float, nullable=False)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)

    sales: Mapped[List['Sale']] = relationship(
        back_populates='product',
        cascade='all, delete-orphan',
    )
    purchases: Mapped[List['Purchase']] = relationship(
        back_populates='product',
        cascade='all, delete-orphan',
    )


class Sale(Base):
    __tablename__ = 'sales'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped['Product'] = relationship(back_populates='sales')
    payments: Mapped[List['Payment']] = relationship(
        back_populates='sale',
        cascade='all, delete-orphan',
    )


class Purchase(Base):
    __tablename__ = 'purchases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped['Product'] = relationship(back_populates='purchases')


class Payment(Base):
    __tablename__ = 'mpesa_payments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sale_id: Mapped[Optional[int]] = mapped_column(ForeignKey('sales.id'), nullable=True)
    mrid: Mapped[Optional[str]] = mapped_column(String(100))
    crid: Mapped[Optional[str]] = mapped_column(String(100))
    trans_code: Mapped[Optional[str]] = mapped_column(String(100))
    trans_amount: Mapped[Optional[float]] = mapped_column(Float)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sale: Mapped[Optional['Sale']] = relationship(back_populates='payments')
