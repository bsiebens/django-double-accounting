from django import template
from django.urls import resolve

register = template.Library()


@register.simple_tag(takes_context=True)
def is_active(context, value):
    url_name = resolve(context.request.path)

    if url_name.url_name.split("_")[0] == "accounts":
        if url_name.kwargs.get("account_type") == value:
            return "is-active"

    elif url_name.url_name.split("_")[0] == value:
        return "is-active"

    return None
