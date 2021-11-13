from graphene_django import DjangoObjectType
from graphene_django.forms.mutation import DjangoModelFormMutation

from ..models import Currency, CurrencyConversion
from ..forms.currency import CurrencyForm

import graphene


class CurrencyType(DjangoObjectType):
    class Meta:
        model = Currency
        fields = ["id", "code", "name"]


class CurrencyMutation(DjangoModelFormMutation):
    currency = graphene.Field(CurrencyType)

    class Meta:
        form_class = CurrencyForm


class Query(graphene.ObjectType):
    currencies = graphene.List(CurrencyType)

    def resolve_currencies(self, info):
        return Currency.objects.order_by("name").all()


class Mutation(graphene.ObjectType):
    currency = CurrencyMutation.Field()
