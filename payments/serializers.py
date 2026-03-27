from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'job',
            'method',
            'amount',
            'transaction_id',
            'status',
            'created_at'
        ]
        read_only_fields = ['status', 'transaction_id']