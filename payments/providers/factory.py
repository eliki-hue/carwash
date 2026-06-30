from django.conf import settings

from .daraja import DarajaProvider
from .jenga import JengaProvider


def get_payment_provider():

    provider = settings.PAYMENT_PROVIDER.lower()

    providers = {
        "daraja": DarajaProvider,
        "jenga": JengaProvider,
    }

    if provider not in providers:
        raise ValueError(f"Unsupported payment provider: {provider}")

    return providers[provider]()