from django.urls import path

from . import views

app_name = 'charger'

urlpatterns = [
  # /charger/
  path('', views.index, name='index'),

  # /charger/login/
  path('login/', views.login, name='login'),

  # /charger/vehicles/
  path('vehicles/', views.vehicles, name='vehicles')
]