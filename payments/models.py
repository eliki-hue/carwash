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
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    mpesa_receipt = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True
    )

    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    checkout_request_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    received_by = models.ForeignKey(
        'users.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    


    class Meta:
        indexes = [
            models.Index(fields=["status", "paid_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["checkout_request_id"]),
        ]



    def __str__(self):
        return f"{self.job} - {self.method} - {self.status}"