from django.db import models
from django.utils import timezone

from .account import Account
from .currency import Currency

import uuid


class Transaction(models.Model):
    date = models.DateField(default=timezone.localdate)
    payee = models.CharField(max_length=250, null=True, blank=True)
    short_description = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "created"]
        get_latest_by = "date"

    def __str__(self):
        return self.short_description


class TransactionLeg(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="transaction_legs")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=20, decimal_places=5)
    currency = models.ForeignKey(Currency, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return "{i.account} {i.amount} {i.currency.code}".format(i=self)
