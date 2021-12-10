from functools import cache
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from django.utils import timezone

from model_utils import FieldTracker
from decimal import Decimal

from .currency import Currency, CurrencyConversion

import uuid


class Budget(models.Model):
    class Period(models.TextChoices):
        DAY = "day", "Day"
        WEEK = "week", "Week"
        MONTH = "month", "Month"
        QUARTER = "quarter", "Quarter"
        HALF_YEAR = "half_year", "Every 6 months"
        YEAR = "year", "Year"

    class AutoBudget(models.TextChoices):
        NO = "no", "No auto-budget"
        ADD = "add", "Add left-over budget to new period"
        FIXED = "fixed", "Fixed budget for each period"

    name = models.CharField(max_length=250)
    is_active = models.BooleanField("is active?", default=True)
    auto_budget = models.CharField(max_length=30, choices=AutoBudget.choices, default=AutoBudget.NO)
    period = models.CharField(max_length=30, choices=Period.choices, default=Period.MONTH, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True, related_name="budgets")
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)

    tracker = FieldTracker()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @cached_property
    def current_period(self):
        return self.get_period_for_date(date=timezone.localdate())

    @cached_property
    def used(self):
        return self.current_period.used

    @cached_property
    def available(self):
        return self.current_period.available

    def get_period_for_date(self, date):
        try:
            return self.periods.get(start_date__lte=date, end_date__gte=date)

        except BudgetPeriod.DoesNotExist:
            return None


class BudgetPeriod(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="periods")
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["budget", "start_date"]
        get_latest_by = "start_date"

    def __str__(self):
        return "{i.budget.name}: {start_date} <> {end_date}".format(
            i=self, start_date=self.start_date.strftime("%d %b %Y"), end_date=self.end_date.strftime("%d %b %Y")
        )

    @cached_property
    def used(self):
        total_used = Decimal(0)

        # Calculate how much is used per currency
        from .transaction import Transaction

        transactions = (
            Transaction.objects.filter(journal_entry__budgets=self.budget, amount__lte=0)
            .values("currency__code")
            .annotate(amount=Coalesce(Sum("amount"), Decimal(0)))
        )

        for currency in transactions:
            amount_in_budget_currency = CurrencyConversion.convert(
                base_currency=currency["currency__code"], target_currency=self.currency, amount=currency["amount"]
            )
            total_used += amount_in_budget_currency

        return total_used

    @cached_property
    def available(self):
        return self.amount + self.used
