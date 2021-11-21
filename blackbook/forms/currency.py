from django import forms
from django.utils import timezone

from blackbook.models.currency import CurrencyConversion

from ..models import Currency


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ["code", "name"]


class CurrencyConversionForm(forms.ModelForm):
    timestamp = forms.DateTimeField(required=False, initial=timezone.now)

    class Meta:
        model = CurrencyConversion
        fields = ["base_currency", "target_currency", "multiplier"]
