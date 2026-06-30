import base64
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache

from .base import PaymentProvider


class DarajaProvider(PaymentProvider):
    """
    Safaricom Daraja STK Push Provider
    """

    TOKEN_CACHE_KEY = "daraja_access_token"
    TOKEN_TTL = 3500

    def __init__(self):
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.oauth_url = settings.MPESA_OAUTH_URL
        self.stk_url = settings.MPESA_STK_URL

    def get_access_token(self):
        token = cache.get(self.TOKEN_CACHE_KEY)

        if token:
            return token

        credentials = (
            f"{settings.MPESA_CONSUMER_KEY}:"
            f"{settings.MPESA_CONSUMER_SECRET}"
        )

        encoded = base64.b64encode(
            credentials.encode()
        ).decode()

        response = requests.get(
            self.oauth_url,
            headers={
                "Authorization": f"Basic {encoded}",
            },
            timeout=30,
        )

        response.raise_for_status()

        token = response.json()["access_token"]

        cache.set(
            self.TOKEN_CACHE_KEY,
            token,
            self.TOKEN_TTL,
        )

        return token

    def stk_push(
        self,
        phone,
        amount,
        reference="CarWash",
        description="Car Wash Payment",
    ):

        access_token = self.get_access_token()

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )

        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": self.callback_url,
            "AccountReference": reference,
            "TransactionDesc": description,
        }

        response = requests.post(
            self.stk_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def query_transaction(self, checkout_request_id):
        """
        We'll implement this later.
        """
        raise NotImplementedError

    def validate_callback(self, payload):
        """
        Add callback signature validation if needed.
        """
        return True

    def parse_callback(self, payload):
        """
        Normalize Daraja callback into a provider-neutral format.
        """

        body = payload["Body"]["stkCallback"]

        result = {
            "provider": "daraja",
            "merchant_request_id": body.get("MerchantRequestID"),
            "checkout_request_id": body.get("CheckoutRequestID"),
            "result_code": body.get("ResultCode"),
            "result_desc": body.get("ResultDesc"),
            "status": (
                "success"
                if body.get("ResultCode") == 0
                else "failed"
            ),
        }

        if body.get("ResultCode") == 0:

            metadata = {}

            for item in body["CallbackMetadata"]["Item"]:
                metadata[item["Name"]] = item.get("Value")

            result.update(
                {
                    "amount": metadata.get("Amount"),
                    "provider_reference": metadata.get(
                        "MpesaReceiptNumber"
                    ),
                    "phone": metadata.get("PhoneNumber"),
                    "transaction_date": metadata.get(
                        "TransactionDate"
                    ),
                }
            )

        return result