from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import Payment
from .serializers import PaymentSerializer
from jobs.models import Job


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related('job')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        job_id = request.data.get('job')
        method = request.data.get('method')

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

        # 🚫 Prevent duplicate payments
        if hasattr(job, 'payment'):
            return Response({"error": "Payment already exists"}, status=400)

        # Auto-set amount from job
        payment = Payment.objects.create(
            job=job,
            method=method,
            amount=job.price,
            status='pending'
        )

        # 💵 CASH FLOW
        if method == 'cash':
            payment.status = 'completed'
            payment.save()

            job.status = 'paid'
            job.save()

        # 📱 M-PESA FLOW (stub for now)
        if method == 'mpesa':
            # TODO: integrate Daraja API
            pass

        serializer = self.get_serializer(payment)
        return Response(serializer.data)