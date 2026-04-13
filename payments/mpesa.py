import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
import base64
from datetime import datetime
from django.core.cache import cache


MPESA_TOKEN_CACHE_KEY = "mpesa_access_token"
MPESA_TOKEN_TTL = 3500
MPESA_SHORTCODE = settings.MPESA_SHORTCODE
MPESA_PASSKEY = settings.MPESA_PASSKEY

def get_access_token():
    token = cache.get(MPESA_TOKEN_CACHE_KEY)
    if token:
        return token

    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    response = requests.get(
        settings.MPESA_OAUTH_URL,
        headers={
            "Authorization": f"Basic {encoded}",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    token = data["access_token"]

    cache.set(MPESA_TOKEN_CACHE_KEY, token, MPESA_TOKEN_TTL)

    return token


    

def stk_push(phone_number, amount):
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()

    MPESA_API_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    # url = f"{settings.MPESA['BASE_URL']}/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://unmisanthropically-transcultural-minnie.ngrok-free.dev/api/payments/callback/",
        "AccountReference": "CarWash",
        "TransactionDesc": "Car Wash Payment",
    }

    response = requests.post(MPESA_API_URL, json=payload, headers=headers)

    return response.json()