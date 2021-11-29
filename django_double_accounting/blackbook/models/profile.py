from django.db import models
from django.conf import settings

from .currency import Currency
from .base import get_default_currency


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    default_currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, default=get_default_currency(as_object=True).id)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
