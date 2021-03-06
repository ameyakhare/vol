import datetime
import decimal
import requests

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .auth import is_authorized
from .models import Owner, Vehicle, ChargeAttempt, ChargePeriod

# OATH Client Info
# This is already public, so you're not stealing anything from me :)
OATH_CLIENT_ID = 'e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e'
OATH_CLIENT_SECRET = 'c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220'

# Session attribute names
SESSION_USERNAME = 'username'
SESSION_TOKEN = 'token'

# Tesla API Paths
TESLA_PATH_OATH = 'https://owner-api.teslamotors.com/oauth/token'
TESLA_PATH_VEHICLES = 'https://owner-api.teslamotors.com/api/1/vehicles'

# Timestamp formats
TIMESTAMP_FORMAT = '%H:%M'
DATETIME_FORMAT = '%m/%d/%y %H:%M'
DATE_FORMAT = '%m %d %y'
MONTH_FORMAT = '%m'
DAY_FORMAT = '%d'
YEAR_FORMAT  = '%y'
HOUR_FORMAT = '%H'
MINUTE_FORMAT = '%M'

class Object:
  def __init__(self):
    pass

def get_owner(user):
  try:
    owner = Owner.objects.get(username=user)
    return owner
  except Owner.DoesNotExist:
    return None

def index(request):
  v = {}
  req = requests.get(
    TESLA_PATH_VEHICLES, 
    headers = {
      'Authorization': 'Bearer ' + request.session[SESSION_TOKEN]
    }
  )

  if req.status_code != 200:
      print('Unable to fetch vehicles for user: ' + request.session[SESSION_USERNAME])
      vehicle_list = []
  else:
      vehicle_list = req.json()['response']

  # Conform to string
  for vehicle in vehicle_list:
    info = Object()
    info.id = str(vehicle['id'])
    info.display_name = vehicle['display_name']
    info.plug_time = datetime.time(hour=19, minute=0).strftime(TIMESTAMP_FORMAT)
    info.unplug_time = datetime.time(hour=6, minute=0).strftime(TIMESTAMP_FORMAT)
    info.checked = False
    v[vehicle['id']] = info
    vehicle['id'] = str(vehicle['id'])

  # The user has requested an update to the charging status of their vehicles.
  user = Owner.objects.get(username=request.session[SESSION_USERNAME])
  if request.method == 'POST':
    for vehicle in vehicle_list:
      # print(type(vehicle))
      vehicle_checked = (vehicle['id'] + "_check") in request.POST

      if vehicle_checked and not Vehicle.objects.filter(owner=user, vehicle_id=vehicle['id']).exists():
        # If the vehicle was checked, make sure its in the db
        new_vehicle = Vehicle(owner=user, vehicle_id=vehicle['id'], name=vehicle['display_name'])
        new_vehicle.plug_time = datetime.datetime.strptime(request.POST[vehicle['id'] + "_plug"], TIMESTAMP_FORMAT).time()
        new_vehicle.unplug_time = datetime.datetime.strptime(request.POST[vehicle['id'] + "_unplug"], TIMESTAMP_FORMAT).time()
        new_vehicle.save()

        print('Adding vehicle: ' + vehicle['display_name'])
      elif vehicle_checked and Vehicle.objects.filter(owner=user, vehicle_id=vehicle['id']).exists():
        # If the vehicle was not checked, make sure its not in the db
        existing_vehicle = Vehicle.objects.get(owner=user, vehicle_id=vehicle['id'])
        existing_vehicle.plug_time = datetime.datetime.strptime(request.POST[vehicle['id'] + "_plug"], TIMESTAMP_FORMAT).time()
        existing_vehicle.unplug_time = datetime.datetime.strptime(request.POST[vehicle['id'] + "_unplug"], TIMESTAMP_FORMAT).time()
        existing_vehicle.save()

        print('Updating vehicle: ' + vehicle['display_name'])
      elif not vehicle_checked and Vehicle.objects.filter(owner=user, vehicle_id=vehicle['id']).exists():
        Vehicle.objects.get(owner=user, vehicle_id=vehicle['id']).delete()

        print('Removing vehicle: ' + vehicle['display_name'])

  vehicle_owner = Owner.objects.get(username=request.session[SESSION_USERNAME])
  vehicle_scheduled = Vehicle.objects.filter(owner=vehicle_owner)

  
  for vehicle in vehicle_scheduled:
    vehicle.str_time = vehicle.plug_time.strftime(TIMESTAMP_FORMAT)
    vehicle.str_unplug_time = vehicle.unplug_time.strftime(TIMESTAMP_FORMAT)
    vid = int(vehicle.vehicle_id)
    v[vid].plug_time = vehicle.str_time
    v[vid].unplug_time = vehicle.str_unplug_time
    v[vid].checked = True

  context = {
    'v': v,
  }
  return render(request, 'charger/index.html', context)

def login(request):
  try:
    if is_authorized(request.session[SESSION_USERNAME], request.session[SESSION_TOKEN]):
      return HttpResponseRedirect(reverse('charger:index'))
  except:
    pass

  if request.method == 'GET':
    return render(request, 'charger/login.html', {})
  
  try:
    user = request.POST['username']
    password = request.POST['password']
  except:
    return render(request, 'charger/login.html', { 
      'error_message': 'Login credentials provided were malformed.'
    })

  req = requests.post(
    TESLA_PATH_OATH, 
    data = {
        'grant_type': 'password', 
        'client_id': OATH_CLIENT_ID, 
        'client_secret': OATH_CLIENT_SECRET, 
        'email': user, 
        'password': password,
    }
  )

  if req.status_code != 200:
    print('Log in failed for user ' + user + ': ' + req.reason)
    return render(request, 'charger/login.html', {
      'error_message': req.reason 
    })

  access_token = req.json()['access_token']
  update = get_owner(user)
  if update:
    update.token = access_token
    update.save()
  else:
    Owner(username=user, token=access_token).save()

  request.session[SESSION_USERNAME] = user
  request.session[SESSION_TOKEN] = access_token
  return HttpResponseRedirect(reverse('charger:index'))

def logout(request):
  del request.session[SESSION_USERNAME]
  del request.session[SESSION_TOKEN]
  return HttpResponseRedirect(reverse('charger:login'))

def savings(request):
  vehicle_owner = Owner.objects.get(username=request.session[SESSION_USERNAME])
  
  # Savings calculations
  charge_attempts = ChargeAttempt.objects.filter(owner=vehicle_owner).order_by('-default_start')
  total_savings = decimal.Decimal(0.0)
  
  num = 0
  for charge_attempt in charge_attempts:
    charge_attempt.default_start_str = charge_attempt.default_start.strftime(DATETIME_FORMAT)
    charge_attempt.default_end_str = charge_attempt.default_end.strftime(DATETIME_FORMAT)
    charge_attempt.day = charge_attempt.default_start.strftime(DAY_FORMAT)
    charge_attempt.month = charge_attempt.default_start.strftime(MONTH_FORMAT)
    charge_attempt.year = charge_attempt.default_start.strftime(YEAR_FORMAT)
    charge_attempt.num = num
    num += 1

    delta = charge_attempt.default_end - charge_attempt.default_start
    charge_attempt.default_cost = charge_attempt.default_price * charge_attempt.default_kwh
    charge_attempt.duration_str = '{}:{}'.format(delta.seconds // 3600, (delta.seconds % 3600) // 60)
    
    charge_periods = ChargePeriod.objects.filter(attempt=charge_attempt).order_by('start')
    charge_attempt.periods = charge_periods

    savings = decimal.Decimal(0.0)

    for charge_period in charge_attempt.periods:
      charge_period.start_str = charge_period.start.strftime(DATETIME_FORMAT)
      charge_period.end_str = charge_period.end.strftime(DATETIME_FORMAT)

      charge_period.beg_day = charge_period.start.strftime(DAY_FORMAT)
      charge_period.beg_month = charge_period.start.strftime(MONTH_FORMAT)
      charge_period.beg_year = charge_period.start.strftime(YEAR_FORMAT)
      charge_period.beg_hour = charge_period.start.strftime(HOUR_FORMAT)
      charge_period.beg_min = charge_period.start.strftime(MINUTE_FORMAT)


      charge_period.end_day = charge_period.end.strftime(DAY_FORMAT)
      charge_period.end_month = charge_period.end.strftime(MONTH_FORMAT)
      charge_period.end_year = charge_period.end.strftime(YEAR_FORMAT)
      charge_period.end_hour = charge_period.end.strftime(HOUR_FORMAT)
      charge_period.end_min = charge_period.end.strftime(MINUTE_FORMAT)

      charge_period.cost = charge_period.price * charge_period.kwh
      charge_period.saving = (charge_attempt.default_price - charge_period.price) * charge_period.kwh
      savings += charge_period.saving

    charge_attempt.savings = savings
    total_savings += savings / 100

  return render(request, 'charger/savings.html', {
    'charge_attempts': charge_attempts,
    'total_savings': total_savings
  })
