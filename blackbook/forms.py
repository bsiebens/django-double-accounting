from django import forms
from django.utils import timezone

from blackbook.models.currency import CurrencyConversion

from .models import Currency


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
    default_currency = forms.ModelChoiceField(queryset=Currency.objects.all())
