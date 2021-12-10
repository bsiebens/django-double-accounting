from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q, Prefetch
from django.shortcuts import render

from ..forms import TransactionFilterForm
from ..charts import TransactionChart
from ..models import get_default_value, TransactionJournal, Transaction, Budget
from ..utilities import calculate_period, set_message_and_redirect, set_message


@login_required
def view(request):
    transaction_journals = TransactionJournal.objects.all()

    period = calculate_period(
        periodicity=get_default_value(key="default_period", default_value="month", user=request.user), start_date=timezone.localdate()
    )

    filter_form = TransactionFilterForm(request.GET or None, initial={"start_date": period["start_date"], "end_date": period["end_date"]})
    if filter_form.is_valid():
        period["start_date"] = filter_form.cleaned_data["start_date"]
        period["end_date"] = filter_form.cleaned_data["end_date"]

        if filter_form.cleaned_data["description"] != "":
            transaction_journals = transaction_journals.filter(
                Q(short_description__icontains=filter_form.cleaned_data["description"])
                | Q(description__icontains=filter_form.cleaned_data["description"])
            )

        if filter_form.cleaned_data["account"] is not None:
            transaction_journals = transaction_journals.filter(transactions__account=filter_form.cleaned_data["account"])

        if filter_form.cleaned_data["tag"] != "":
            tags = filter_form.cleaned_data["tag"].split(" ")

            # Filtered out for now because of bug #2.
            # transaction_journals = transaction_journals.filter(tags__name__in=tags)

    transaction_journals = (
        transaction_journals.filter(date__range=(period["start_date"], period["end_date"]))
        .prefetch_related("transactions", "transactions__account", "transactions__currency", "tags", "budgets")
        .order_by("-date")
    )
    transactions = (
        Transaction.objects.filter(journal_entry__in=transaction_journals)
        .select_related("journal_entry", "account", "currency")
        .prefetch_related("journal_entry__tags")
        .prefetch_related(Prefetch("journal_entry__budgets", queryset=Budget.objects.select_related("currency")))
    )

    charts = {
        "expense_payee_chart": TransactionChart(data=transactions, payee=True).generate_json(),
        "expense_payee_chart_count": transactions.filter(amount__lt=0).exclude(journal_entry__payee=None).count(),
        "expense_budget_chart": TransactionChart(data=transactions, expenses_budget=True).generate_json(),
        "expense_budget_chart_count": len([item for item in transactions if item.amount < 0 and item.journal_entry.budgets.count != 0]),
        "expense_tag_chart": TransactionChart(data=transactions, expenses_tag=True).generate_json(),
        "expense_tag_chart_count": len([item for item in transactions if item.amount < 0 and item.journal_entry.tags.count != 0]),
    }

    return render(
        request,
        "blackbook/transactions/list.html",
        {"filter_form": filter_form, "charts": charts, "period": period, "transaction_journals": transaction_journals},
    )


@login_required
def add_edit(request):
    pass


@login_required
def delete(request):
    if request.method == "POST":
        journal_entry = TransactionJournal.objects.get(uuid=request.POST.get("transaction_uuid"))
        journal_entry.delete()

        return set_message_and_redirect(
            request,
            "s|Transaction {journal_entry.short_description} was succesfully deleted".format(journal_entry=journal_entry),
            reverse("blackbook:dashboard"),
        )
    else:
        return set_message_and_redirect(request, "w|You are not allowed to access this page like this", reverse("blackbook:dashboard"))
