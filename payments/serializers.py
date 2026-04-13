from rest_framework import serializers
from .models import Payment
from jobs.models import Job


class PaymentSerializer(serializers.ModelSerializer):
    #  RELATED DISPLAY FIELDS (IMPORTANT)
    service_name = serializers.CharField(source="job.service.name", read_only=True)
    vehicle_type = serializers.CharField(source="job.vehicle_type.name", read_only=True)
    plate_number = serializers.CharField(source="job.plate_number", read_only=True)

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["status", "amount"]

    def validate(self, data):
        method = data.get("method")
        job = data.get("job")

        #  Prevent duplicate payment
        if Payment.objects.filter(job=job).exists():
            raise serializers.ValidationError("This job is already paid")

        #  Ensure job is completed before payment
        if job.status != "completed":
            raise serializers.ValidationError("Only completed jobs can be paid")

        #  Manual MPESA requires transaction ID
        if method == "mpesa_manual" and not data.get("transaction_id"):
            raise serializers.ValidationError("Transaction ID required")

        #  STK requires phone number
        if method == "mpesa_stk" and not data.get("phone_number"):
            raise serializers.ValidationError("Phone number required")

        return data

    def create(self, validated_data):
        method = validated_data["method"]
        job = validated_data["job"]

        #  FORCE CORRECT AMOUNT (SECURITY)
        validated_data["amount"] = job.price

        #  HANDLE PAYMENT METHODS
        if method == "cash":
            validated_data["status"] = "success"

        elif method == "mpesa_manual":
            validated_data["status"] = "success"

        elif method == "mpesa_stk":
            validated_data["status"] = "pending"

        payment = super().create(validated_data)

        # UPDATE JOB STATUS
        if payment.status == "success":
            job.status = "paid"
            job.save(update_fields=["status"])

        return payment