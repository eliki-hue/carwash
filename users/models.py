from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('owner', 'Owner'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)

    def __str__(self):
        return self.get_full_name() or self.username