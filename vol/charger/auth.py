from .models import Owner

def is_authorized(user, token):
  if not user or not token:
    return False

  try:
    owner = Owner.objects.get(username=user)
  except:
    owner = None

  # Redirect if unauthorized user is trying to access a regular page.
  if not owner or token != owner.token:
    return False

  return True