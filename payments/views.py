from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Payment
from .serializers import PaymentSerializer
from jobs.models import Job
from .mpesa import stk_push


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related(
        "job",
        "job__service",
        "job__vehicle_type"
    )
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    #  CREATE PAYMENT (CASH + MANUAL MPESA)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        return Response({
            "message": "Payment recorded successfully",
            "data": PaymentSerializer(payment).data
        })

    #  STK PUSH
    @action(detail=False, methods=['post'])
    def mpesa_stkpush(self, request):
        job_id = request.data.get('job')
        phone_number = request.data.get('phone_number')

        if not job_id or not phone_number:
            return Response({"error": "Job and phone number required"}, status=400)

        job = get_object_or_404(Job, id=job_id)

        #  Prevent duplicate payment
        if hasattr(job, 'payment'):
            return Response({"error": "Job already has a payment"}, status=400)

        #  Only completed jobs
        if job.status != "completed":
            return Response({"error": "Only completed jobs can be paid"}, status=400)

        #  CALL MPESA
        response = stk_push(phone_number, job.price)

        checkout_id = response.get("CheckoutRequestID")

        if not checkout_id:
            return Response({
                "error": "Failed to initiate STK push",
                "mpesa_response": response
            }, status=400)

        #  SAVE PAYMENT
        payment = Payment.objects.create(
            job=job,
            amount=job.price,
            method="mpesa_stk",
            phone_number=phone_number,
            checkout_request_id=checkout_id,
            status="pending",
        )

        return Response({
            "message": "STK push initiated",
            "checkout_request_id": checkout_id
        })
    


@api_view(['POST'])
@permission_classes([AllowAny])  # Safaricom won't send auth
def mpesa_callback(request):
    data = request.data

    try:
        stk_callback = data["Body"]["stkCallback"]
        checkout_id = stk_callback["CheckoutRequestID"]
        result_code = stk_callback["ResultCode"]

        payment = Payment.objects.filter(
            checkout_request_id=checkout_id
        ).select_related("job").first()

        if not payment:
            return Response({"message": "Payment not found"}, status=404)

        #  FAILED PAYMENT
        if result_code != 0:
            payment.status = "failed"
            payment.save(update_fields=["status"])
            return Response({"message": "Payment failed"})

        #  SUCCESS PAYMENT
        metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

        receipt = None

        for item in metadata:
            if item.get("Name") == "MpesaReceiptNumber":
                receipt = item.get("Value")

        with transaction.atomic():
            payment.status = "success"
            payment.transaction_id = receipt
            payment.save(update_fields=["status", "transaction_id"])

            #  UPDATE JOB
            job = payment.job
            job.status = "paid"
            job.save(update_fields=["status"])

        return Response({"message": "Payment successful"})

    except Exception as e:
        return Response({"error": str(e)}, status=500)