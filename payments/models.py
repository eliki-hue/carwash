from django.db import models
from jobs.models import Job


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa_manual', 'M-Pesa Manual'),
        ('mpesa_stk', 'M-Pesa STK Push'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    job = models.OneToOneField(Job, on_delete=models.CASCADE)

    method = models.CharField(max_length=20, choices=METHOD_CHOICES)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    #  Common
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    #  Manual MPESA 
    transaction_id = models.CharField(max_length=100, null=True, blank=True)

    #  STK PUSH
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.job} - {self.method} - {self.status}"