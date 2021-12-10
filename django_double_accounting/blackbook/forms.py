from django import forms
from django.utils import timezone, safestring

from mptt.forms import TreeNodeChoiceField

from .models import Currency, CurrencyConversion, Account, Budget

import re


class DateInput(forms.DateInput):
    input_type = "date"


class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, name, to_python_function, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)

        self._name = name
        self._list = data_list
        self.attrs.update({"list": "list__%s" % self._name})
        self.to_python_function = to_python_function

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % self._name

        for item in self._list:
            data_list += '<option value="%s">%s</option>' % (item, item)

        data_list += "</datalist>"

        return safestring.mark_safe(text_html + data_list)

    def to_python(self, value):
        return self.to_python_function(value)


def accountstring_to_account(value):
    try:
        return Account.objects.get(accountsstring=value)

    except Account.DoesNotExist:
        return None


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ["code", "name"]


class CurrencyConversionForm(forms.ModelForm):
    timestamp = forms.DateTimeField(required=False, initial=timezone.now)

    class Meta:
        model = CurrencyConversion
        fields = ["base_currency", "target_currency", "multiplier"]


class ProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    default_currency = forms.ModelChoiceField(queryset=Currency.objects.all(), blank=False)
    default_period = forms.ChoiceField(choices=Budget.Period.choices)


class AccountForm(forms.ModelForm):
    type = forms.ChoiceField(choices=Account.AccountType.choices, initial=Account.AccountType.ASSET_ACCOUNT)
    parent = TreeNodeChoiceField(queryset=Account.objects.filter(is_active=True), empty_label="None", required=False)

    class Meta:
        model = Account
        fields = ["parent", "currencies", "name", "type", "is_active", "include_on_net_worth", "include_on_dashboard", "iban"]
        widgets = {
            "currencies": forms.CheckboxSelectMultiple(),
        }


class TransactionFilterForm(forms.Form):
    start_date = forms.DateField(widget=DateInput, required=False)
    end_date = forms.DateField(widget=DateInput, required=False)
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search description", "size": 40}))
    account = TreeNodeChoiceField(queryset=Account.objects.filter(is_active=True), empty_label="None", required=False)
    tag = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "Search tags (split by space)"}))
    budget = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(TransactionFilterForm, self).__init__(*args, **kwargs)


class TransactionJournalForm(forms.Form):
    short_description = forms.CharField()
    description = forms.CharField(required=False, widget=forms.Textarea)
    date = forms.DateField(initial=timezone.now, widget=DateInput)
    tags = forms.CharField(required=False, help_text="Split tags by spaces.")
    add_new = forms.BooleanField(required=False, initial=False, help_text="After saving, display this form again to add a new transaction.")
    display = forms.BooleanField(required=False, initial=True, help_text="After saving, display this form again to review this transaction.")


class TransactionForm(forms.Form):
    account = TreeNodeChoiceField(queryset=Account.objects.filter(is_active=True), empty_label=None, required=True)
    amount = forms.DecimalField(max_digits=10, decimal_places=5)
    currency = forms.ModelChoiceField(queryset=Currency.objects.order_by("code").all())
