from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Prefetch, Sum, Count
from django.db.models.functions import Coalesce

from ..charts import AccountChart
from ..models import get_default_value, get_default_currency, Transaction, TransactionJournal, Account, CurrencyConversion, BudgetPeriod
from ..utilities import display_period, calculate_period

from decimal import Decimal


@login_required
def dashboard(request):
    # TODO - Rewrite this page to use less queries on the model side as those scale with additional models
    # Especially around transactions/amounts/budgets/conversions

    period = get_default_value(key="default_period", default_value="month", user=request.user)
    currency = get_default_currency(user=request.user)

    net_worth_transactions = (
        Transaction.objects.filter(account__is_active=True, account__include_on_net_worth=True)
        .filter(journal_entry__date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True))
        .select_related("journal_entry", "account", "currency")
        .prefetch_related(Prefetch("journal_entry__transactions", queryset=Transaction.objects.select_related("account")))
        .prefetch_related("journal_entry__tags")
        .order_by("-journal_entry__date")
    )

    accounts = Account.objects.filter(is_active=True, include_on_net_worth=True, include_on_dashboard=True).prefetch_related("transactions")
    accounts = [account for account in accounts if account.is_leaf_node()]

    budgets = BudgetPeriod.objects.filter(start_date__lte=timezone.localdate(), end_date__gte=timezone.localdate()).select_related("currency")

    data = {
        "totals": {
            "period": {"in": {}, "out": {}, "total": {}},
            "net_worth": Transaction.objects.filter(account__is_active=True, account__include_on_net_worth=True)
            .select_related("currency")
            .values("currency__code")
            .annotate(total=Coalesce(Sum("amount"), Decimal(0))),
        },
        "period": display_period(periodicty=period, start_date=timezone.localdate()),
        "budget": {"currency": currency, "used": Decimal(0), "available": Decimal(0)},
        "charts": {
            "account_chart": AccountChart(
                data=net_worth_transactions.filter(account__include_on_dashboard=True),
                accounts=accounts,
                start_date=calculate_period(periodicity=period, start_date=timezone.localdate())["start_date"],
                end_date=calculate_period(periodicity=period, start_date=timezone.localdate())["end_date"],
            ).generate_json(),
        },
        "transaction_count": TransactionJournal.objects.filter(
            date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True)
        ).count(),
        "payee_count": len(
            list(
                set(
                    [
                        item["payee"]
                        for item in TransactionJournal.objects.filter(
                            date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True)
                        )
                        .exclude(payee=None)
                        .values("payee")
                    ]
                )
            )
        ),
        "most_used_payee": TransactionJournal.objects.exclude(payee=None)
        .filter(date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True))
        .values("payee")
        .annotate(Count("pk"))
        .order_by("-pk__count")
        .first()["payee"],
        "highest_amount": Transaction.objects.filter(
            journal_entry__date__range=calculate_period(periodicity=period, start_date=timezone.localdate(), as_tuple=True)
        )
        .order_by("-amount")
        .select_related("currency")
        .first(),
        "most_used_tag": TransactionJournal.tags.most_common()[0],
    }

    for transaction in net_worth_transactions:
        if transaction.amount < 0:
            data["totals"]["period"]["out"][transaction.currency.code] = (
                data["totals"]["period"]["out"].get(transaction.currency.code, 0) + transaction.amount
            )
        else:
            data["totals"]["period"]["in"][transaction.currency.code] = (
                data["totals"]["period"]["in"].get(transaction.currency.code, 0) + transaction.amount
            )

        data["totals"]["period"]["total"][transaction.currency.code] = (
            data["totals"]["period"]["total"].get(transaction.currency.code, 0) + transaction.amount
        )

    for budget in budgets:
        data["budget"]["used"] += CurrencyConversion.convert(base_currency=budget.currency, target_currency=currency, amount=budget.used)
        data["budget"]["available"] += CurrencyConversion.convert(base_currency=budget.currency, target_currency=currency, amount=budget.available)

    return render(request, "blackbook/dashboard.html", {"data": data})
