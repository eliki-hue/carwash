from abc import ABC, abstractmethod


class PaymentProvider(ABC):

    @abstractmethod
    def stk_push(
        self,
        phone: str,
        amount: float,
        reference: str,
        description: str = "",
    ):
        """
        Initiate payment.
        """
        raise NotImplementedError

    @abstractmethod
    def query_transaction(self, reference: str):
        """
        Check transaction status.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_callback(self, payload: dict):
        """
        Validate callback payload.
        """
        raise NotImplementedError

    @abstractmethod
    def parse_callback(self, payload: dict):
        """
        Return normalized callback data.
        """
        raise NotImplementedError