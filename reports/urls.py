from django.urls import path
from .views import (
    DailyReportView,
    PaymentBreakdownView,
    StaffPerformanceView,
    MonthlyPerformanceView,
)

urlpatterns = [
    path('daily/', DailyReportView.as_view(), name='daily-report'),
    path('payments/', PaymentBreakdownView.as_view(), name='payment-breakdown'),
    path('staff-performance/', StaffPerformanceView.as_view(), name='staff-performance'),
    path('monthly/', MonthlyPerformanceView.as_view(), name='monthly-performance'),
]