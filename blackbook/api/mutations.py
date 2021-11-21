from graphene_django.forms.mutation import DjangoModelFormMutation

from . import types
from .. import models
from ..forms.currency import CurrencyConversionForm, CurrencyForm

import graphene


class CurrencyFormMutation(DjangoModelFormMutation):
    currency = graphene.Field(types.CurrencyType)

    class Meta:
        form_class = CurrencyForm


class CurrencyConversionFormMutation(DjangoModelFormMutation):
    currency_conversion = graphene.Field(types.CurrencyConversionType)

    class Meta:
        form_class = CurrencyConversionForm

    def resolve_currency_conversion(self, info, **kwargs):
        return self.currencyConversion


class DeleteCurrency(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID()

    @classmethod
    def mutate(cls, root, info, **kwargs):
        obj = models.Currency.objects.get(pk=kwargs["id"])
        obj.delete()

        return cls(ok=True)


class DeleteCurrencyConversion(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID()

    @classmethod
    def mutate(cls, root, info, **kwargs):
        obj = models.CurrencyConversion.objects.get(pk=kwargs["id"])
        obj.delete()

        return cls(ok=True)
