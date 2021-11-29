from graphene_django.forms.mutation import DjangoFormMutation, DjangoModelFormMutation

from . import types
from .. import models
from ..forms import CurrencyConversionForm, CurrencyForm, ProfileForm

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


class ProfileFormMutation(DjangoFormMutation):
    user = graphene.Field(types.UserType)

    class Meta:
        form_class = ProfileForm

    def perform_mutate(form, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Not logged in")

        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.save()

        user.userprofile.default_currency = form.cleaned_data["default_currency"]
        user.userprofile.save()

        return ProfileFormMutation(user=user)


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
