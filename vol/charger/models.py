from django.db import models

# Create your models here.

class Owner(models.Model):
  username = models.CharField(max_length=100, unique=True)
  token = models.CharField(max_length=100)

  def __str__(self):
    return self.username + ': ' + self.token[:5] + '...'

class Vehicle(models.Model):
  owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
  vehicle_id = models.CharField(max_length=50)
  name = models.CharField(max_length=50)

  def __str__(self):
    return self.owner.username + ': ' + self.vehicle_id