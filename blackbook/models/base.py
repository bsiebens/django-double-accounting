from django.conf import settings


def get_default_value(key, default_value=None, user=None):
    try:
        profile = user.userprofile

        return getattr(profile, key.lower(), default_value)
    except:
        return getattr(settings, key.upper(), default_value)


def get_default_currency(user=None, as_object=False):
    default_currency = get_default_value("default_currency", "EUR", user)

    if not as_object and type(default_currency) != str:
        return default_currency.code
    elif as_object and type(default_currency) == str:
        from .currency import Currency

        try:
            return Currency.objects.get(code=default_currency)
        except Currency.DoesNotExist:
            return Currency()

    else:
        return default_currency
