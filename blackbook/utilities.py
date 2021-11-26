from django.template.defaultfilters import slugify

import re


def format_iban(value, grouping=4):
    if value is None:
        return None

    value = value.upper().replace(" ", "").replace("-", "")

    return " ".join(value[i : i + grouping] for i in range(0, len(value), grouping))


def validate_iban(iban):
    _country2length = dict(
        AL=28,
        AD=24,
        AT=20,
        AZ=28,
        BE=16,
        BH=22,
        BA=20,
        BR=29,
        BG=22,
        CR=21,
        HR=21,
        CY=28,
        CZ=24,
        DK=18,
        DO=28,
        EE=20,
        FO=18,
        FI=18,
        FR=27,
        GE=22,
        DE=22,
        GI=23,
        GR=27,
        GL=18,
        GT=28,
        HU=28,
        IS=26,
        IE=22,
        IL=23,
        IT=27,
        KZ=20,
        KW=30,
        LV=21,
        LB=28,
        LI=21,
        LT=20,
        LU=20,
        MK=19,
        MT=31,
        MR=27,
        MU=30,
        MC=27,
        MD=24,
        ME=22,
        NL=18,
        NO=15,
        PK=24,
        PS=29,
        PL=28,
        PT=25,
        RO=24,
        SM=27,
        SA=24,
        RS=22,
        SK=24,
        SI=19,
        ES=24,
        SE=24,
        CH=21,
        TN=24,
        TR=26,
        AE=23,
        GB=22,
        VG=24,
    )

    # Check if empty
    if iban == "":
        return True

    # Ensure upper alphanumeric input.
    iban = iban.replace(" ", "").replace("\t", "")
    if not re.match(r"^[\dA-Z]+$", iban):
        return False
    # Validate country code against expected length.
    if len(iban) != _country2length[iban[:2]]:
        return False
    # Shift and convert.
    iban = iban[4:] + iban[:4]
    digits = int("".join(str(int(ch, 36)) for ch in iban))  # BASE 36: 0..9,A..Z -> 0..35
    return digits % 97 == 1


def unique_slugify(instance, value, slug_field_name="slug", queryset=None, slug_separator="-"):
    """
    Calculates and stores a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug, limiting its length if necessary.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create the queryset if one wasn't explicitly provided and exclude the
    # current instance from the queryset.
    if queryset is None:
        queryset = instance.__class__._default_manager.all()

        from .models import Account

        if instance.__class__.__base__ == Account:
            queryset = instance.__class__.__base__._default_manager.all()

    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = "%s%s" % (slug_separator, next)
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[: slug_len - len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = "%s%s" % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator="-"):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    separator = separator or ""
    if separator == "-" or not separator:
        re_sep = "-"
    else:
        re_sep = "(?:-|%s)" % re.escape(separator)
    # Remove multiple instances and if an alternate separator is provided,
    # replace the default '-' separator.
    if separator != re_sep:
        value = re.sub("%s+" % re_sep, separator, value)
    # Remove separator from the beginning and end of the slug.
    if separator:
        if separator != "-":
            re_sep = re.escape(separator)
        value = re.sub(r"^%s+|%s+$" % (re_sep, re_sep), "", value)
    return value
