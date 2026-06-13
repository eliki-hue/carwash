from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import status
from django.utils import timezone


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
        if job.status not in ["in_progress", "completed"]:
            return Response(
                {"error": "Job must be in progress"},
                status=400
            )

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
    

    @action(detail=False, methods=['get'], url_path=r'status/(?P<checkout_id>[^/.]+)')
    def status(self, request, checkout_id=None):
        payment = Payment.objects.filter(
            checkout_request_id=checkout_id
        ).first()

        if not payment:
            return Response({"status": "not_found"}, status=404)

        return Response({
            "status": payment.status,
            "mpesa_receipt": payment.mpesa_receipt,
        })


    @action(detail=False, methods=["post"])
    def retry_stk(self, request):
        job_id = request.data.get("job")

        if not job_id:
            return Response(
                {"error": "Job ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        job = get_object_or_404(Job, id=job_id)

        # --------------------------------------------------
        # 1. Job already paid?
        # --------------------------------------------------
        if job.status == "paid":
            return Response(
                {"error": "Job is already paid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if job.payments.filter(status="success").exists():
            return Response(
                {"error": "Successful payment already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # 2. Pending request already exists?
        # --------------------------------------------------
        if job.payments.filter(status="pending").exists():
            return Response(
                {"error": "Pending payment request already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # 3. Get last STK attempt
        # --------------------------------------------------
        last_payment = (
            job.payments
            .filter(method="mpesa_stk")
            .order_by("-created_at")
            .first()
        )

        if not last_payment:
            return Response(
                {"error": "No previous STK payment found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # 4. Allow retry only for failed attempts
        # --------------------------------------------------
        if last_payment.status not in [
            "failed",
            "cancelled",
            "expired",
        ]:
            return Response(
                {
                    "error":
                    f"Cannot retry payment with status '{last_payment.status}'"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # 5. Send new STK push
        # --------------------------------------------------
        mpesa_response = stk_push(
            phone_number=last_payment.phone_number,
            amount=job.price
        )

        checkout_request_id = mpesa_response.get(
            "CheckoutRequestID"
        )

        if not checkout_request_id:
            return Response(
                {
                    "error": "Failed to initiate STK push",
                    "mpesa_response": mpesa_response,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # 6. Create NEW payment attempt
        # --------------------------------------------------
        payment = Payment.objects.create(
            job=job,
            amount=job.price,
            method="mpesa_stk",
            phone_number=last_payment.phone_number,
            checkout_request_id=checkout_request_id,
            status="pending",
        )

        return Response(
            {
                "message": "STK retry initiated",
                "payment_id": payment.id,
                "checkout_request_id": checkout_request_id,
            },
            status=status.HTTP_201_CREATED,
        )

    


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def mpesa_callback(request):

    try:
        callback = request.data.get("Body", {}).get("stkCallback", {})

        checkout_request_id = callback.get("CheckoutRequestID")
        result_code = callback.get("ResultCode")

        if not checkout_request_id:
            return Response(
                {"error": "Missing CheckoutRequestID"},
                status=400
            )

        payment = (
            Payment.objects
            .select_related("job")
            .filter(
                checkout_request_id=checkout_request_id
            )
            .first()
        )

        if not payment:
            return Response(
                {"error": "Payment not found"},
                status=404
            )

        # -------------------------------------------------
        # Prevent duplicate callback processing
        # -------------------------------------------------

        if payment.status == "success":
            return Response(
                {"message": "Callback already processed"}
            )

        # -------------------------------------------------
        # FAILED / CANCELLED / EXPIRED
        # -------------------------------------------------

        if result_code != 0:

            if result_code == 1032:
                payment.status = "cancelled"

            elif result_code == 1037:
                payment.status = "expired"

            else:
                payment.status = "failed"

            payment.save(update_fields=["status"])

            return Response({
                "message": payment.status
            })

        # -------------------------------------------------
        # SUCCESS PAYMENT
        # -------------------------------------------------

        metadata = callback.get(
            "CallbackMetadata",
            {}
        ).get("Item", [])

        receipt = None
        amount = None
        phone_number = None
        transaction_date = None

        for item in metadata:

            name = item.get("Name")
            value = item.get("Value")

            if name == "MpesaReceiptNumber":
                receipt = value

            elif name == "Amount":
                amount = value

            elif name == "PhoneNumber":
                phone_number = value

            elif name == "TransactionDate":
                transaction_date = value

        with transaction.atomic():

            payment.status = "success"
            payment.mpesa_receipt = receipt

            if amount:
                payment.amount = amount

            if phone_number:
                payment.phone_number = str(phone_number)

            payment.paid_at = timezone.now()

            payment.save()

            job = payment.job

            if job.status != "paid":
                job.status = "paid"
                job.save(update_fields=["status"])

        return Response({
            "message": "Payment successful",
            "receipt": receipt,
            "amount": amount,
        })

    except Exception as e:

        return Response(
            {
                "error": str(e)
            },
            status=500
        )
@api_view(['POST'])
@permission_classes([AllowAny])  # Safaricom won't send auth
@authentication_classes([])
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
            payment.mpesa_receipt = receipt
            payment.save(update_fields=["status", "mpesa_receipt"])

            #  UPDATE JOB
            job = payment.job
            job.status = "paid"
            job.save(update_fields=["status"])

        return Response({"message": "Payment successful"})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
