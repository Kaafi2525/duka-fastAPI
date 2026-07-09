import math
import base64
import requests
import re
from datetime import datetime
from requests.auth import HTTPBasicAuth
from config import settings


consumer_key = settings.mpesa_consumer_key
consumer_secret = settings.mpesa_consumer_secret
saf_short_code = settings.mpesa_short_code
saf_stk_push_url = settings.mpesa_stk_push_url
saf_api_url = settings.mpesa_auth_url
saf_passkey = settings.mpesa_passkey
saf_callback_url = settings.mpesa_callback_url.replace("/stk_call_back", "/mpesa/stk-call-back")


def _normalize_phone_number(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    if digits.startswith("254") and len(digits) == 12:
        return digits
    raise ValueError("Phone number must be in format 2547XXXXXXXX")

# time will be sent to stk push as part of the password, so we need to generate it in the format yyyymmddhhmmss
# the request is for sending http like axios
# math is for converting into an integer
# base 64 is for hashing for security
# http basicAuth is used to get token for authentication


def get_mpesa_access_token():
    if not consumer_key or not consumer_secret:
        raise ValueError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set in .env")
    try:
        res = requests.get(
            saf_api_url,
            auth=HTTPBasicAuth(consumer_key, consumer_secret),
            timeout=30,
        )
        res.raise_for_status()
        payload = res.json()
        token = payload.get("access_token")
        if not token:
            raise ValueError(f"Failed to get M-Pesa token: {payload}")

       
    except Exception as e:
        print(str(e), "error getting access token")
        raise e

    return token


def generate_password(timestamp: str):
        if not saf_passkey:
            raise ValueError("MPESA_PASSKEY must be set in .env")
        password_str = saf_short_code + saf_passkey + timestamp
        password_bytes = password_str.encode()
        return base64.b64encode(password_bytes).decode("utf-8")

def make_stk_push( payload):
        amount = float(payload['amount'])
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        phone_number = _normalize_phone_number(payload['phone_number'])
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        access_token = get_mpesa_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        push_data = {
            "BusinessShortCode": saf_short_code,
            "Password": generate_password(timestamp),
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": math.ceil(amount),
            "PartyA": phone_number,
            "PartyB": saf_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": saf_callback_url,
            "AccountReference": str(payload.get('sale_id', 'SALE'))[:12],
            "TransactionDesc": "description of the transaction",
        }

        response = requests.post(
            saf_stk_push_url,
            json=push_data,
            headers=headers,
            timeout=30)
        if response.status_code >= 400:
            try:
                error_payload = response.json()
            except Exception:
                error_payload = {"raw": response.text}
            raise ValueError(f"M-Pesa STK rejected request: {error_payload}")

        response_data = response.json()

        return response_data

# make_stk_push({
#     "amount": 1,
#     "phone_number": "254792213329",
#     "sale_id": "SALE001"

# })
