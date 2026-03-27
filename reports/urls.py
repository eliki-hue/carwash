from django.urls import path
from .views import (
    DailyReportView,
    PaymentBreakdownView,
    StaffPerformanceView
)

urlpatterns = [
    path('daily/', DailyReportView.as_view()),
    path('payments/', PaymentBreakdownView.as_view()),
    path('staff/', StaffPerformanceView.as_view()),
]