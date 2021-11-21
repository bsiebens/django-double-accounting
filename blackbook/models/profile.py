from django.db import models
from django.conf import settings

from .currency import Currency


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    default_currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
