from django.contrib import admin

from .models import Owner, Vehicle, ChargeAttempt, ChargePeriod

# Register your models here.

admin.site.register(Owner)
admin.site.register(Vehicle)
admin.site.register(ChargeAttempt)
admin.site.register(ChargePeriod)
