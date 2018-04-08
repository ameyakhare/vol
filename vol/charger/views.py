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
DATE_FORMAT = '%m/%d/%y'

def get_owner(user):
  try:
    owner = Owner.objects.get(username=user)
    return owner
  except Owner.DoesNotExist:
    return None

def index(request):
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
    vehicle['id'] = str(vehicle['id'])

  # The user has requested an update to the charging status of their vehicles.
  user = Owner.objects.get(username=request.session[SESSION_USERNAME])
  if request.method == 'POST':
    for vehicle in vehicle_list:
      if vehicle['id'] in request.POST and not Vehicle.objects.filter(owner=user, vehicle_id=vehicle['id']).exists():
        # If the vehicle was checked, make sure its in the db
        Vehicle(owner=user, vehicle_id=vehicle['id'], name=vehicle['display_name']).save()

        print('Adding vehicle: ' + vehicle['display_name'])
      elif vehicle['id'] not in request.POST and Vehicle.objects.filter(owner=user, vehicle_id=vehicle['id']).exists():
        # If the vehicle was not checked, make sure its not in the db
        Vehicle.objects.filter(owner=user, vehicle_id=vehicle['id']).delete()

        print('Removing vehicle: ' + vehicle['display_name'])

  vehicle_owner = Owner.objects.get(username=request.session[SESSION_USERNAME])
  vehicle_known = Vehicle.objects.filter(owner=vehicle_owner)

  vehicle_scheduled = []
  for vehicle in vehicle_known:
    vehicle_scheduled.append(vehicle.vehicle_id)

  context = {
    'vehicle_list': vehicle_list,
    'vehicle_scheduled': vehicle_scheduled,
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
  vehicle_scheduled = Vehicle.objects.filter(owner=vehicle_owner)

  if request.method == 'POST':
    for vehicle in vehicle_scheduled:
      if vehicle.vehicle_id in request.POST:
        vehicle.plug_time = datetime.datetime.strptime(request.POST[vehicle.vehicle_id], TIMESTAMP_FORMAT).time()
        vehicle.save()

  for vehicle in vehicle_scheduled:
    vehicle.str_time = vehicle.plug_time.strftime(TIMESTAMP_FORMAT)

  # Savings calculations
  charge_attempts = ChargeAttempt.objects.filter(owner=vehicle_owner).order_by('default_start')
  total_savings = decimal.Decimal(0.0)
  
  for charge_attempt in charge_attempts:
    charge_attempt.default_start_str = charge_attempt.default_start.strftime(DATETIME_FORMAT)
    charge_attempt.default_end_str = charge_attempt.default_end.strftime(DATETIME_FORMAT)
    charge_attempt.default_start_date = charge_attempt.default_start.strftime(DATE_FORMAT)

    delta = charge_attempt.default_end - charge_attempt.default_start
    charge_attempt.default_cost = charge_attempt.default_price * charge_attempt.default_kwh
    charge_attempt.duration_str = '{}:{}'.format(delta.seconds // 3600, (delta.seconds % 3600) // 60)
    
    charge_periods = ChargePeriod.objects.filter(attempt=charge_attempt).order_by('start')
    charge_attempt.periods = charge_periods

    savings = decimal.Decimal(0.0)

    for charge_period in charge_attempt.periods:
      charge_period.start_str = charge_period.start.strftime(DATETIME_FORMAT)
      charge_period.end_str = charge_period.end.strftime(DATETIME_FORMAT)

      charge_period.cost = charge_period.price * charge_period.kwh
      charge_period.saving = (charge_attempt.default_price - charge_period.price) * charge_period.kwh
      savings += charge_period.saving

    charge_attempt.savings = savings
    total_savings += savings / 100

  return render(request, 'charger/savings.html', {
    'vehicle_scheduled': vehicle_scheduled,
    'charge_attempts': charge_attempts,
    'total_savings': total_savings
  })
