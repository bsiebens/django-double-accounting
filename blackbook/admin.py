from django.contrib import admin

from . import models


class CurrencyConversionsInline(admin.TabularInline):
    model = models.CurrencyConversion
    extra = 0
    fields = ["multiplier", "target_currency", "timestamp"]
    fk_name = "base_currency"


@admin.register(models.Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "name"]
    list_display_links = ["code"]
    search_fields = ["code", "name"]
    inlines = [CurrencyConversionsInline]
    fieldsets = [
        ["General information", {"fields": ["code", "name"]}],
    ]
