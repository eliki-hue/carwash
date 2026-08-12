from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, Count
from django.utils.timezone import now
from calendar import month_name, monthrange
from django.db.models.functions import ExtractMonth, ExtractYear

from jobs.models import Job
from payments.models import Payment
from users.permissions import IsManagerOrOwner
from expenses.models import Expense
from payments.models import Payment
from django.utils.timezone import now

permission_classes = [IsAuthenticated, IsManagerOrOwner]
from datetime import date


from django.db.models.functions import TruncDate
from rest_framework import status





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


class ProfitReportView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrOwner]

    def get(self, request):
        today = now().date()

        revenue = (
            Payment.objects.filter(
                status="success",
                created_at__date=today
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        expenses = (
            Expense.objects.filter(
                expense_date=today
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        profit = revenue - expenses

        return Response({
            "date": today,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit
        })



class DailyBreakdownView(APIView):
    """
    Daily sales, expenses and profit for a selected calendar month.

    GET:
        /api/reports/daily-breakdown/?year=2026&month=8
    """

    permission_classes = [
        IsAuthenticated,
        IsManagerOrOwner,
    ]

    def get(self, request):

        today = now().date()

        # ==================================================
        # YEAR
        # ==================================================

        year_param = request.query_params.get("year")

        try:
            year = int(year_param) if year_param else today.year
        except (TypeError, ValueError):
            return Response(
                {
                    "error": "Invalid year."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # MONTH
        # ==================================================

        month_param = request.query_params.get("month")

        try:
            month = int(month_param) if month_param else today.month
        except (TypeError, ValueError):
            return Response(
                {
                    "error": "Invalid month."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if month < 1 or month > 12:
            return Response(
                {
                    "error": "Month must be between 1 and 12."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==================================================
        # MONTH RANGE
        # ==================================================

        first_day = date(year, month, 1)

        last_day = date(
            year,
            month,
            monthrange(year, month)[1],
        )

        # ==================================================
        # SUCCESSFUL PAYMENTS
        #
        # IMPORTANT:
        # Revenue is based on paid_at, not created_at.
        # ==================================================

        payments = (
            Payment.objects
            .filter(
                status="success",
                paid_at__isnull=False,
                paid_at__date__gte=first_day,
                paid_at__date__lte=last_day,
            )
            .annotate(
                day=TruncDate("paid_at")
            )
            .values("day")
            .annotate(
                revenue=Sum("amount"),
                payment_count=Count("id"),
            )
        )

        payment_by_day = {
            item["day"]: {
                "revenue": item["revenue"] or 0,
                "payment_count": item["payment_count"] or 0,
            }
            for item in payments
        }

        # ==================================================
        # EXPENSES
        # ==================================================

        expenses = (
            Expense.objects
            .filter(
                expense_date__gte=first_day,
                expense_date__lte=last_day,
            )
            .values("expense_date")
            .annotate(
                total_expenses=Sum("amount"),
                expense_count=Count("id"),
            )
        )

        expense_by_day = {
            item["expense_date"]: {
                "expenses": item["total_expenses"] or 0,
                "expense_count": item["expense_count"] or 0,
            }
            for item in expenses
        }

        # ==================================================
        # BUILD DAILY DATA
        # ==================================================

        days = []

        total_revenue = 0
        total_expenses = 0
        total_payments = 0
        total_expense_records = 0

        days_in_month = monthrange(year, month)[1]

        for day_number in range(1, days_in_month + 1):

            report_date = date(
                year,
                month,
                day_number,
            )

            payment_data = payment_by_day.get(
                report_date,
                {
                    "revenue": 0,
                    "payment_count": 0,
                },
            )

            expense_data = expense_by_day.get(
                report_date,
                {
                    "expenses": 0,
                    "expense_count": 0,
                },
            )

            revenue = payment_data["revenue"] or 0
            expenses_total = expense_data["expenses"] or 0

            profit = revenue - expenses_total

            payment_count = payment_data["payment_count"]
            expense_count = expense_data["expense_count"]

            total_revenue += revenue
            total_expenses += expenses_total
            total_payments += payment_count
            total_expense_records += expense_count

            days.append(
                {
                    "date": report_date.isoformat(),
                    "day": day_number,
                    "revenue": float(revenue),
                    "expenses": float(expenses_total),
                    "profit": float(profit),
                    "payment_count": payment_count,
                    "expense_count": expense_count,
                }
            )

        # ==================================================
        # MONTH SUMMARY
        # ==================================================

        total_profit = total_revenue - total_expenses

        return Response(
            {
                "year": year,
                "month": month,
                "days_in_month": days_in_month,

                "summary": {
                    "revenue": float(total_revenue),
                    "expenses": float(total_expenses),
                    "profit": float(total_profit),
                    "payment_count": total_payments,
                    "expense_count": total_expense_records,
                },

                "days": days,
            }
        )