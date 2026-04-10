from django.db import models

# Create your models here.
class Service(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Minutes")



class ServicePricing(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    vehicle_type = models.ForeignKey('vehicles.VehicleType', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('service', 'vehicle_type')

    def __str__(self):
        return f"{self.service} - {self.vehicle_type} - {self.price}"