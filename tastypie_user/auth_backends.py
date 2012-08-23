#encoding:utf8
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import  User

class ApiKeyBackend(ModelBackend):
    def authenticate(self, username=None, api_key=None):
        if not username or not api_key:
            return None
        try:
            return User.objects.get(username=username, api_key=api_key)
        except User.DoesNotExist:
            return None

class EmailBackend(ModelBackend):
    def authenticate(self, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

