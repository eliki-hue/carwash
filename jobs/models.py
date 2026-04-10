from django.db import models


class Job(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
    ]

    plate_number = models.CharField(max_length=20, db_index=True)

    vehicle_type = models.ForeignKey(
        'vehicles.VehicleType',
        on_delete=models.PROTECT
    )

    service = models.ForeignKey(
        'services.Service',
        on_delete=models.PROTECT
    )

    assigned_staff = models.ForeignKey(
        'users.User',
        null=True,
        on_delete=models.SET_NULL
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.plate_number} - {self.service}"