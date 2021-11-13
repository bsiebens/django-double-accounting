from django.db import models
from django.db.models import Q
from django.utils import timezone

from decimal import Decimal


class Currency(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=250)

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper()

        super("Currency", self).save(*args, **kwargs)
