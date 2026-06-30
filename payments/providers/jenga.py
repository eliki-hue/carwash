from .base import PaymentProvider


class JengaProvider(PaymentProvider):

    def stk_push(
        self,
        phone,
        amount,
        reference,
        description=""
    ):
        raise NotImplementedError("Coming soon")

    def query_transaction(self, reference):
        raise NotImplementedError

    def validate_callback(self, payload):
        return True

    def parse_callback(self, payload):

        return {}