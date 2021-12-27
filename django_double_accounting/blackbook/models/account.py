from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.functional import cached_property
from django.core.exceptions import ValidationError

from localflavor.generic.models import IBANField
from mptt.models import MPTTModel, TreeForeignKey
from decimal import Decimal

from .currency import Currency
from ..utilities import unique_slugify

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
    icon = models.CharField(max_length=50, null=True, blank=True)
    iban = IBANField("IBAN", null=True, blank=True)
    accountstring = models.CharField("Account", max_length=250, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["parent", "name"], name="unique_account_name_for_parent")]

    @cached_property
    def balance(self):
        return self.balance_until_date()

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
            "equity": "fa-coins",
        }

        self.clean()

        unique_slugify(self, self.name)
        self.icon = type_to_icon[self.type]

        super(Account, self).save(*args, **kwargs)

        # After saving we need to update the accountstring and save again
        self.accountstring = "{type}:{accountstring}".format(
            type=self.get_type_display(),
            accountstring=":".join([account["name"] for account in self.get_ancestors(include_self=True).values("name")]),
        )
        super(Account, self).save()

    def balance_until_date(self, date=timezone.localdate()):
        from .transaction import Transaction

        transactions = (
            Transaction.objects.filter(journal_entry__date__lte=date)
            .filter(account__in=self.get_descendants(include_self=True))
            .values("currency__code")
            .order_by("currency__code")
            .annotate(amount=Coalesce(Sum("amount"), Decimal(0)))
        )

        if len(transactions) != 0:
            return [(currency["amount"], currency["currency__code"]) for currency in transactions]

        return [(0, currency.code) for currency in self.currencies.all()]

    @classmethod
    def get_or_create(cls, account_string, return_last=True):
        account_tree = account_string.split(":")
        accounts = []
        parent_account = None
        account_type = None

        for index, account_name in enumerate(account_tree):
            if index == 0:
                # If index == 0, we don't create an account but verify if it matches any of the account types.
                if account_name.lower() not in cls.AccountType.values:
                    raise ValidationError("Incorrect account type set as first value.")

                account_type = account_name.lower()

            else:
                account, created = cls.objects.get_or_create(name=account_name, parent=parent_account, type=account_type)
                accounts.append((account, created))
                parent_account = account

        if return_last:
            return accounts[-1][0]
        return accounts
