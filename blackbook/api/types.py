from django.contrib.auth import get_user_model

from graphene_django import DjangoObjectType

from .. import models

import graphene


class CurrencyType(DjangoObjectType):
    class Meta:
        model = models.Currency
        fields = ["id", "code", "name"]


class CurrencyConversionType(DjangoObjectType):
    class Meta:
        model = models.CurrencyConversion
        fields = ["id", "base_currency", "target_currency", "multiplier", "timestamp"]


class AmountType(graphene.ObjectType):
    amount = graphene.Decimal()
    currency = graphene.Field(CurrencyType)


class UserType(DjangoObjectType):
    default_currency = graphene.Field(CurrencyType, description="default currency")

    class Meta:
        model = get_user_model()

    def resolve_default_currency(self, info):
        return self.userprofile.default_currency
