from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, Count
from django.utils.timezone import now

from jobs.models import Job
from payments.models import Payment
from users.permissions import IsManagerOrOwner

permission_classes = [IsAuthenticated, IsManagerOrOwner]


class DailyReportView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrOwner]


    def get(self, request):
        today = now().date()

        jobs = Job.objects.filter(created_at__date=today)

        total_cars = jobs.count()

        total_revenue = jobs.filter(status='paid').aggregate(
            total=Sum('price')
        )['total'] or 0

        return Response({
            "date": today,
            "total_cars": total_cars,
            "total_revenue": total_revenue
        })


class PaymentBreakdownView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrOwner]


    def get(self, request):
        today = now().date()

        payments = Payment.objects.filter(created_at__date=today)

        breakdown = payments.values('method').annotate(
            total=Sum('amount'),
            count=Count('id')
        )

        return Response(breakdown)


class StaffPerformanceView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrOwner]


    def get(self, request):
        today = now().date()

        data = Job.objects.filter(
            created_at__date=today,
            status='completed'
        ).values(
            'assigned_staff__username'
        ).annotate(
            total_jobs=Count('id'),
            total_revenue=Sum('price')
        ).order_by('-total_jobs')

        return Response(data)