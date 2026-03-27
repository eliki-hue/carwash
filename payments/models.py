from django.db import models

# Create your models here.
class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
    ]

    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)