from datetime import datetime

from django.http import HttpResponseRedirect
from django.urls import reverse

from ..auth import is_authorized
from ..models import Owner

# Session expiration. User will be logged out after 10 minutes of inactivity.
SESSION_MAX_SECONDS = 10*60

# Session attribute names
SESSION_USERNAME = 'username'
SESSION_TOKEN = 'token'

class SessionCheckMiddleware(object):
    def __init__(self, get_response):
      self.get_response = get_response

    def __call__(self, request):
      try:
        username = request.session[SESSION_USERNAME]
        token = request.session[SESSION_TOKEN]
      except:
        username = ''
        token = ''

      # Redirect if unauthorized user is trying to access a regular page.
      if not is_authorized(username, token) and reverse('charger:login') not in request.path:
        return HttpResponseRedirect(reverse('charger:login'))

      request.session.set_expiry(SESSION_MAX_SECONDS)
      return self.get_response(request)
