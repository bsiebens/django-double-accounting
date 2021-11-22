from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from localflavor.generic.models import IBANField
from mptt.models import MPTTModel, TreeForeignKey
from decimal import Decimal

from .currency import Currency
from .base import get_default_currency

import uuid


class Account(MPTTModel):
    class AccountType(models.TextChoices):
        ASSET_ACCOUNT = "assets", "Assets"
        INCOME_ACCOUNT = "income", "Income"
        EXPENSE_ACCOUNT = "expenses", "Expenses"
        LIABILITIES_ACCOUNT = "liabilities", "Liabilities"
        CASH_ACCOUNT = "cash", "Cash"
        EQUITY_ACCOUNT = "equity", "Equity"

    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    name = models.CharField(max_length=200)
    slug = models.SlugField(db_index=True, unique=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)
    is_active = models.BooleanField("active?", default=True)
    include_on_net_worth = models.BooleanField(
        "include in net worth calculations?", default=True, help_text="Include this account when calculating the overall net worth?"
    )
    include_on_dashboard = models.BooleanField("include on dashboad?", default=True, help_text="Include this account on the dashboard?")
    currencies = models.ManyToManyField(
        Currency,
        blank=True,
        help_text="Optional, in case currencies are selected, the account will be restricted to accepting transactions only in this currency.",
    )
    type = models.CharField(max_length=50, choices=AccountType.choices)
    icon = models.CharField(max_length=50)
    iban = IBANField("IBAN", null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["parent", "name"], name="unique_account_name_for_parent")]

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent is not None:
            if self.type != self.parent.type:
                raise ValidationError(
                    {"type": "Account type must be the same as the account type of the parent account (%s)" % self.parent.get_type_display()}
                )

    def save(self, *args, **kwargs):
        type_to_icon = {
            "assets": "fa-landmark",
            "income": "fa-donate",
            "expenses": "fa-file-invoice-dollar",
            "liabilities": "fa-home",
            "cash": "fa-coins",
        }

        self.clean()

        # unique_slugify(self, self.name)
        self.icon = type_to_icon[self.type]

        super(Account, self).save(*args, **kwargs)
