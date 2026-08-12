from django.urls import path
from .views import (
    DailyReportView,
    PaymentBreakdownView,
    StaffPerformanceView,
    MonthlyPerformanceView,
    ProfitReportView, DailyBreakdownView,
)

urlpatterns = [
    path('daily/', DailyReportView.as_view(), name='daily-report'),
    path('payments/', PaymentBreakdownView.as_view(), name='payment-breakdown'),
    path('staff-performance/', StaffPerformanceView.as_view(), name='staff-performance'),
    path('monthly/', MonthlyPerformanceView.as_view(), name='monthly-performance'),
    path("profit/", ProfitReportView.as_view(), name="profit-report"),
    path("daily-breakdown/",DailyBreakdownView.as_view(), name="daily-breakdown",),
]