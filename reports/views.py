from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, Count
from django.utils.timezone import now
from calendar import month_name
from django.db.models.functions import ExtractMonth, ExtractYear

from jobs.models import Job
from payments.models import Payment
from users.permissions import IsManagerOrOwner

permission_classes = [IsAuthenticated, IsManagerOrOwner]


# reports/views.py - Update DailyReportView
class DailyReportView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrOwner]

    def get(self, request):
        # Get date from query params or use today
        date_str = request.query_params.get('date')
        if date_str:
            from datetime import datetime
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = now().date()

        jobs = Job.objects.filter(created_at__date=report_date)

        total_cars = jobs.count()
        total_revenue = jobs.filter(status='paid').aggregate(
            total=Sum('price')
        )['total'] or 0

        return Response({
            "date": report_date,
            "total_cars": total_cars,
            "total_revenue": total_revenue
        })



class MonthlyPerformanceView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrOwner]

    def get(self, request):
        year = request.query_params.get('year')
        
        try:
            year = int(year) if year else now().year
        except ValueError:
            year = now().year

        # Get all paid jobs for the selected year
        jobs = Job.objects.filter(
            status='paid',
            completed_at__year=year
        )

        # Aggregate by month
        monthly_data = jobs.annotate(
            month=ExtractMonth('completed_at')
        ).values('month').annotate(
            total_jobs=Count('id'),
            total_revenue=Sum('price')
        ).order_by('month')

        # Create array for all 12 months
        result = []
        for month in range(1, 13):
            data = next((d for d in monthly_data if d['month'] == month), None)
            result.append({
                "month": month_name[month],
                "year": year,
                "total_jobs": data['total_jobs'] if data else 0,
                "total_revenue": float(data['total_revenue']) if data and data['total_revenue'] else 0,
            })

        return Response(result)

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