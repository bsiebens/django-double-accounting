from django.db.models import ProtectedError
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Prefetch
from django.db.models.functions import Coalesce

from decimal import Decimal

from ..utilities import calculate_period, set_message_and_redirect

from ..models import Account, Transaction, get_default_value
from ..forms import AccountForm
from ..charts import AccountChart, TransactionChart


@login_required
def view(request, account_type=None, uuid=None):
    if uuid is not None:
        period = get_default_value("default_period", default_value="month", user=request.user)
        period = calculate_period(period, start_date=timezone.localdate())

        account = get_object_or_404(Account.objects.prefetch_related("currencies"), uuid=uuid)
        transactions = (
            Transaction.objects.filter(account__in=account.get_descendants(include_self=True))
            .filter(journal_entry__date__range=(period["start_date"], period["end_date"]))
            .select_related("journal_entry", "account", "currency")
            .prefetch_related(Prefetch("journal_entry__transactions", queryset=Transaction.objects.select_related("account")))
            .prefetch_related("journal_entry__tags")
            .order_by("-journal_entry__date")
        )

        period_data = {"in": {}, "out": {}, "balance": {}}
        for currency in transactions.filter(amount__gte=0).values("currency__code").annotate(total=Coalesce(Sum("amount"), Decimal(0))):
            currency_code = currency["currency__code"]
            period_data["in"][currency_code] = period_data["in"].get(currency_code, 0) + currency["total"]
            period_data["balance"][currency_code] = period_data["balance"].get(currency_code, 0) + currency["total"]

        for currency in transactions.filter(amount__lte=0).values("currency__code").annotate(total=Coalesce(Sum("amount"), Decimal(0))):
            currency_code = currency["currency__code"]
            period_data["out"][currency_code] = period_data["out"].get(currency_code, 0) + currency["total"]
            period_data["balance"][currency_code] = period_data["balance"].get(currency_code, 0) + currency["total"]

        charts = {
            "account_chart": AccountChart(
                data=transactions, accounts=[account], start_date=period["start_date"], end_date=period["end_date"]
            ).generate_json(),
            "expense_payee_chart": TransactionChart(data=transactions, payee=True).generate_json(),
            "expense_payee_chart_count": len([item for item in transactions if item.amount > 0]),
            "expense_budget_chart_count": 0,  # len([item for item in transactions if item.amount < 0 and item.journal_entry.budget is not None]),
            "expense_tag_chart": TransactionChart(data=transactions, expenses_tag=True).generate_json(),
            "expense_tag_chart_count": len([item for item in transactions if item.amount < 0 and item.journal_entry.tags.count != 0]),
        }

        return render(
            request,
            "blackbook/accounts/detail.html",
            {"account": account, "transactions": transactions, "period": period, "period_data": period_data, "charts": charts},
        )

    else:
        account_types = {
            "assets": {"name": "asset accounts", "icon": "fa-landmark", "total": {}},
            "income": {"name": "income accounts", "icon": "fa-donate", "total": {}},
            "expenses": {"name": "expense accounts", "icon": "fa-file-invoice-dollar", "total": {}},
            "liabilities": {"name": "liabilities", "icon": "fa-home", "total": {}},
            "cash": {"name": "cash accounts", "icon": "fa-coins", "total": {}},
        }

        accounts = Account.objects.filter(type=account_type).prefetch_related("currencies")
        account_type = account_types[account_type]

        for account in accounts:
            if account.is_root_node():
                for currency in account.balance:
                    account_type["total"][currency[1]] = account_type["total"].get(currency[1], 0) + currency[0]

        return render(request, "blackbook/accounts/list.html", {"accounts": accounts, "account_type": account_type})


@login_required
def add_edit(request, uuid=None):
    account = Account()

    if uuid is not None:
        account = get_object_or_404(Account.objects.prefetch_related("currencies"), uuid=uuid)

    account_form = AccountForm(request.POST or None, instance=account)

    if request.POST and account_form.is_valid():
        account = account_form.save()

        return set_message_and_redirect(
            request,
            "s|Account {account.name} ({account.accountstring}) was created succesfully".format(account=account),
            reverse("blackbook:dashboard"),
        )

    return render(request, "blackbook/accounts/form.html", {"account_form": account_form, "account": account})


@login_required
def delete(request):
    if request.method == "POST":
        account = Account.objects.get(uuid=request.POST.get("account_uuid"))

        try:
            account.delete()
            return set_message_and_redirect(
                request,
                "s|Account {account.name} ({account.accountstring}) was sucessfully deleted".format(account=account),
                reverse("blackbook:dashboard"),
            )

        except ProtectedError:
            return set_message_and_redirect(
                request,
                "f|Cannot remove {account.name} ({account.accountstring}), there are still transactions linked to this account".format(
                    account=account
                ),
                reverse("blackbook:dashboard"),
            )

    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this", reverse("blackbook:dashboard"))
