from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render

from ..forms import TransactionFilterForm
from ..models import get_default_value, TransactionJournal
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
        .prefetch_related("transactions", "transactions__account", "transactions__currency", "tags")
        .order_by("-date")
    )

    return render(
        request, "blackbook/transactions/list.html", {"filter_form": filter_form, "period": period, "transaction_journals": transaction_journals}
    )


@login_required
def add_edit(request):
    pass


@login_required
def delete(request):
    pass
