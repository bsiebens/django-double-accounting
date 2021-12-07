from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import base
from django.utils import timezone

from taggit.managers import TaggableManager

from .account import Account
from .currency import Currency, CurrencyConversion
from .base import get_default_currency

import uuid
import operator


class TransactionJournal(models.Model):
    date = models.DateField(default=timezone.localdate)
    payee = models.CharField(max_length=250, null=True, blank=True)
    short_description = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    uuid = models.UUIDField("UUID", default=uuid.uuid4, editable=False, db_index=True, unique=True)
    tags = TaggableManager(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "created"]
        get_latest_by = "date"

    def __str__(self):
        return self.short_description

    def _create_transactions(self, transactions, user=None):
        if len(transactions) == 0:
            raise ValidationError("Transaction list supplied was empty.")

        # In order to proceed we will convert all values in the transactions dictionary to proper objects
        for transaction in transactions:
            if type(transaction["currency"]) == str and transaction["currency"] != "" and transaction["currency"] is not None:
                transaction["currency"], created = Currency.objects.get_or_create(code=transaction["currency"])

            if "account_currency" in transaction.keys():
                if (
                    type(transaction["account_currency"]) == str
                    and transaction["account_currency"] != ""
                    and transaction["account_currency"] is not None
                ):
                    transaction["account_currency"], created = Currency.objects.get_or_create(code=transaction["account_currency"])

            if type(transaction["account"]) == str:
                # Replace the string with : format into the right account name (or create as needed)
                account = Account.get_or_create(transaction["account"])
                transaction["account"] = account

        # Run checks and calculate amounts
        total_amount_per_currency = {}
        account_currencies = {}
        empty_transaction_index = -1
        default_currency, created = Currency.objects.get_or_create(code=get_default_currency(user=user))

        for index, transaction in enumerate(transactions):
            if transaction["amount"] == "" or transaction["amount"] is None:
                if empty_transaction_index != -1:
                    raise ValidationError("Only 1 transaction is allow to have an empty amount set")

                empty_transaction_index = index

                currencies = account_currencies.get(transaction["account"], [currency.code for currency in transaction["account"].currencies.all()])
                if len(currencies) == 0:
                    currencies = [default_currency]

                # setting currency on the transaction (will be easier later on) and adding it already in the list
                transaction["currency"] = currencies[0]
                total_amount_per_currency[currencies[0]] = total_amount_per_currency.get(currencies[0], 0)

            else:
                total_amount_per_currency[transaction["currency"]] = total_amount_per_currency.get(transaction["currency"], 0) + transaction["amount"]

        # We choose the currency with the highest value as the baseline currency
        baseline_currency = max(total_amount_per_currency.items(), key=operator.itemgetter(1))[0]
        baseline_amount = 0

        for currency, amount in total_amount_per_currency.items():
            baseline_amount += CurrencyConversion.convert(base_currency=currency, target_currency=baseline_currency, amount=amount)

        if empty_transaction_index != -1:
            transactions[empty_transaction_index]["amount"] = (
                CurrencyConversion.convert(base_currency=baseline_currency, target_currency=transaction["currency"], amount=baseline_amount) * -1
            )
            baseline_amount = 0

        if baseline_amount != 0:
            raise ValidationError(
                "Sum of all transactions doesn't reach 0 (current difference {amount} {currency}".format(
                    amount=baseline_amount, currency=baseline_currency
                )
            )

        transaction_entries = []
        for transaction in transactions:
            currencies = account_currencies.get(transaction["account"], [currency.code for currency in transaction["account"].currencies.all()])
            if len(currencies) == 0:
                currencies = [default_currency]

            transaction_amount = transaction["amount"]
            transaction_currency = transaction["currency"]

            if transaction["currency"] not in currencies:
                if transaction["account_currency"] in currencies:
                    transaction_amount = transaction["account_amount"]
                    transaction_currency = transaction["account_currency"]

                else:
                    transaction_amount = CurrencyConversion.convert(
                        base_currency=transaction["currency"], target_currency=currencies[0], amount=transaction["amount"]
                    )

            transaction_entries.append(
                Transaction(account=transaction["account"], amount=transaction_amount, currency=transaction_currency, journal_entry=self)
            )

        return transaction_entries

    @classmethod
    def create(cls, short_description, transactions, date=timezone.localdate(), description=None, payee=None, user=None):
        journal_entry = cls.objects.create(short_description=short_description, date=date, description=description, payee=payee)

        transaction_entries = journal_entry._create_transactions(transactions=transactions, user=user)
        Transaction.objects.bulk_create(transaction_entries)

        return journal_entry


class Transaction(models.Model):
    journal_entry = models.ForeignKey(TransactionJournal, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions")
    amount = models.DecimalField(max_digits=20, decimal_places=5)
    currency = models.ForeignKey(Currency, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["amount", "currency"]

    def __str__(self):
        return "{i.account} {i.amount} {i.currency.code}".format(i=self)
