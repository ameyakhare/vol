from django.urls import path

from . import views

app_name = 'charger'

urlpatterns = [
  # /charger/
  path('', views.index, name='index'),

  # /charger/login/
  path('login/', views.login, name='login'),

  # /charger/logout/
  path('logout/', views.logout, name='logout'),

  # /charger/savings/
  path('savings/', views.savings, name='savings')
]