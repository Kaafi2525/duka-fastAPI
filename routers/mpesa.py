from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import get_db
from mpesa import make_stk_push
from jsonmap import PaymentGetMap
from models import Payment

from routers.generate_pdf import generate_pdf
from routers.send_email import send_email


router = APIRouter(prefix="/mpesa", tags=["mpesa"])


@router.post("/stk-push")
def stk_push(payload: dict, db: Session = Depends(get_db)):
    try:
        print("Received STK push request:", payload)
        mock_mode = bool(payload.get("mock"))

        if mock_mode:
            stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            response = {
                "MerchantRequestID": f"MOCK-MRID-{stamp}",
                "CheckoutRequestID": f"MOCK-CRID-{stamp}",
                "ResponseDescription": "Mock STK push accepted for local testing",
            }
        else:
            response = make_stk_push(payload)

        payment = Payment(
            sale_id=payload.get("sale_id"),
            phone_number=str(payload.get("phone_number", "")),
            trans_amount=float(payload.get("amount", 0)),
            mrid=response.get("MerchantRequestID"),
            crid=response.get("CheckoutRequestID"),
            status="pending",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "message": "Mock STK push recorded" if mock_mode else "STK push sent",
            "payment_id": payment.id,
            "mock": mock_mode,
            "mpesa_response": response,
        }

    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stk-call-back")
def saf_callback(payload: dict, db: Session = Depends(get_db)):
    print("Received SAF callback:", payload)

    try:
        body = payload.get("Body", {})
        stk_callback = body.get("stkCallback", {})

        result_code = stk_callback.get("ResultCode")
        mrid = stk_callback.get("MerchantRequestID")
        crid = stk_callback.get("CheckoutRequestID")

        payment = db.execute(
            select(Payment).where(Payment.mrid == mrid, Payment.crid == crid)
        ).scalar_one_or_none()

        if not payment:
            return {"message": "Payment not found"}

        if result_code == 0:
            callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
            for item in callback_metadata:
                name = item.get("Name")
                value = item.get("Value")
                if name == "MpesaReceiptNumber":
                    payment.trans_code = value
                elif name == "Amount":
                    payment.trans_amount = value
                elif name == "PhoneNumber":
                    payment.phone_number = str(value)

            payment.status = "completed"

            email_result = send_email(
                "customer@gmail.com",
                "Payment Successful",
                f"""
Hello,

Your payment was successful.

Transaction Code: {payment.trans_code}
Amount: {payment.trans_amount}
Phone Number: {payment.phone_number}

Thank you for using Moha Duka POS.
""",
            )
            if isinstance(email_result, dict) and not email_result.get("success", True):
                print("Email send warning:", email_result)

            text = f"""
Payment Receipt

Transaction Code: {payment.trans_code}
Amount: {payment.trans_amount}
Phone Number: {payment.phone_number}
Status: {payment.status}

Thank you for your payment!
"""
            generate_pdf(text, f"{payment.trans_code}.pdf")
        else:
            payment.status = "failed"
            print("Payment failed")

        db.commit()

    except Exception as e:
        db.rollback()
        print("Error processing callback:", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Callback received"}


@router.get("/payments", response_model=List[PaymentGetMap])
def get_payments(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    sale_id: int | None = Query(default=None),
    phone_number: str | None = Query(default=None),
):
    query = select(Payment)
    if status:
        query = query.where(Payment.status == status)
    if sale_id is not None:
        query = query.where(Payment.sale_id == sale_id)
    if phone_number:
        query = query.where(Payment.phone_number == phone_number)

    query = query.order_by(Payment.created_at.desc())
    return db.execute(query).scalars().all()


@router.get("/payments/{payment_id}", response_model=PaymentGetMap)
def get_payment_by_id(payment_id: int, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/payments/stats")
def get_payment_stats(db: Session = Depends(get_db)):
    total_payments = db.execute(select(func.count(Payment.id))).scalar_one()
    completed_payments = db.execute(
        select(func.count(Payment.id)).where(Payment.status == "completed")
    ).scalar_one()
    failed_payments = db.execute(
        select(func.count(Payment.id)).where(Payment.status == "failed")
    ).scalar_one()
    total_collected = db.execute(
        select(func.coalesce(func.sum(Payment.trans_amount), 0.0)).where(
            Payment.status == "completed"
        )
    ).scalar_one()

    success_rate = (completed_payments / total_payments * 100) if total_payments else 0.0

    return {
        "total_payments": total_payments,
        "completed_payments": completed_payments,
        "failed_payments": failed_payments,
        "success_rate_percent": round(success_rate, 2),
        "total_collected": float(total_collected),
    }
