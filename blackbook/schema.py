import graphene

from .api import types, mutations
from . import models


class Mutation(graphene.ObjectType):
    currency = mutations.CurrencyFormMutation.Field()
    currency_conversion = mutations.CurrencyConversionFormMutation.Field()
    delete_currency = mutations.DeleteCurrency.Field()
    delete_currency_conversion = mutations.DeleteCurrencyConversion.Field()


class Query(graphene.ObjectType):
    currencies = graphene.List(types.CurrencyType)
    currency_conversions = graphene.List(types.CurrencyConversionType)

    def resolve_currencies(self, info):
        return models.Currency.objects.order_by("code", "name").all()

    def resolve_currency_conversions(self, info):
        return models.CurrencyConversion.objects.order_by("-timestamp").all()


schema = graphene.Schema(query=Query, mutation=Mutation)
