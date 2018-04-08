import datetime

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
  plug_time = models.TimeField(default=datetime.time(hour=19, minute=0))
  unplug_time = models.TimeField(default=datetime.time(hour=6, minute=0))

  def __str__(self):
    return self.owner.username + ': ' + self.vehicle_id +  ' @ ' + self.plug_time.strftime('%H:%M')

class ChargeAttempt(models.Model):
  owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
  vehicle_name = models.CharField(max_length=50)
  default_start = models.DateTimeField()
  default_end = models.DateTimeField()
  default_kwh = models.DecimalField(max_digits=6, decimal_places=3, default=0.0)
  default_price = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

  def __str__(self):
    return self.vehicle_name + ' @ ' + self.default_start.strftime('%m/%d/%y %H:%M') + ' for ' + str(self.default_price) + '/kwh'

class ChargePeriod(models.Model):
  attempt = models.ForeignKey(ChargeAttempt, on_delete=models.CASCADE)
  start = models.DateTimeField()
  end = models.DateTimeField()
  kwh = models.DecimalField(max_digits=6, decimal_places=3, default=0.0)
  price = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

  def __str__(self):
    return self.start.strftime('%m/%d/%y %H:%M') + ' to ' + self.end.strftime('%m/%d/%y %H:%M') + ' for ' + str(self.price) + '/kwh'