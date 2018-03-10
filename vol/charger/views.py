import requests

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import Owner, Vehicle

# OATH Client Info
# This is already public, so you're not stealing anything from me :)
OATH_CLIENT_ID = 'e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e'
OATH_CLIENT_SECRET = 'c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220'

# Tesla API Paths
TESLA_PATH_OATH = 'https://owner-api.teslamotors.com/oauth/token'

def index(request):
  return render(request, 'charger/index.html', {})

def login(request):
  try:
    user = request.POST['username']
    password = request.POST['password']
  except:
    return render(request, 'charger/index.html', { 
      'error_message': 'Form data is malformed.' 
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
    return render(request, 'charger/index.html', {
      'error_message': req.reason 
    })

  access_token = req.json()['access_token']
  if Owner.objects.filter(username=user).exists():
    update = Owner.objects.get(username=user)
    update.token = access_token
    update.save()
  else:
    update = Owner(username=user, token=access_token)
    update.save()

  # set session with username at this point
  return HttpResponseRedirect(reverse('charger:vehicles'))

def vehicles(request):
  vehicle_owner = Owner.objects.get(username='fakeuser')
  vehicle_list = Vehicle.objects.filter(owner=vehicle_owner)
  context = {
    'vehicle_list': vehicle_list,
  }
  return render(request, 'charger/vehicles.html', context)