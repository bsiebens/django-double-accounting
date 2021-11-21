import graphene

from .api import types, mutations
from . import models


class Mutation(graphene.ObjectType):
    currency = mutations.CurrencyFormMutation.Field()
    currency_conversion = mutations.CurrencyConversionFormMutation.Field()

    update_profile = mutations.UpdateProfileMutation.Field()

    delete_currency = mutations.DeleteCurrency.Field()
    delete_currency_conversion = mutations.DeleteCurrencyConversion.Field()


class Query(graphene.ObjectType):
    currencies = graphene.List(types.CurrencyType)
    currency_conversions = graphene.List(types.CurrencyConversionType)
    profile = graphene.Field(types.UserType)

    def resolve_currencies(self, info):
        return models.Currency.objects.order_by("code", "name").all()

    def resolve_currency_conversions(self, info):
        return models.CurrencyConversion.objects.order_by("-timestamp").all()

    def resolve_profile(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in!")

        return user


schema = graphene.Schema(query=Query, mutation=Mutation)
