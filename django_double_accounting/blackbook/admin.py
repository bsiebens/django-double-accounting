from django.contrib import admin
from django.utils.html import format_html

from mptt.admin import MPTTModelAdmin
from taggit_helpers.admin import TaggitListFilter

from .utilities import format_iban

from . import models


class CurrencyConversionsInline(admin.TabularInline):
    model = models.CurrencyConversion
    extra = 0
    fields = ["multiplier", "target_currency", "timestamp"]
    fk_name = "base_currency"


@admin.register(models.Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["pk", "code", "name"]
    list_display_links = ["code"]
    search_fields = ["code", "name"]
    inlines = [CurrencyConversionsInline]
    fieldsets = [
        ["General information", {"fields": ["code", "name"]}],
    ]


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = "Name"

    list_display = ["pk", "get_full_name", "user", "default_currency", "default_period", "created", "modified"]
    list_display_links = ["get_full_name"]
    ordering = ["user"]
    search_fields = ["user__first_name", "user__last_name", "user__username"]
    raw_id_fields = ["user", "default_currency"]
    list_filter = ["default_currency"]
    fieldsets = [["General information", {"fields": ["user", "default_currency", "default_period"]}]]
    readonly_fields = ["created", "modified"]


@admin.register(models.Account)
class AccountAdmin(MPTTModelAdmin):
    def display_iban(self, obj):
        return format_iban(obj.iban)

    def list_currencies(self, obj):
        currencies = obj.currencies.order_by("code").all()

        if len(currencies) == 0:
            return "-"
        return ", ".join([currency.code for currency in currencies])

    def display_balances(self, obj):
        balances = obj.balance

        if len(balances) != 0:
            return format_html("<br />".join(["{amount} {currency}".format(amount=item[0], currency=item[1]) for item in obj.balance]))

        return "-"

    display_iban.short_description = "IBAN"
    list_currencies.short_description = "Currency"
    display_balances.short_description = "Balance"

    list_display = [
        "pk",
        "name",
        "type",
        "display_iban",
        "list_currencies",
        "display_balances",
        "is_active",
        "include_on_net_worth",
        "include_on_dashboard",
        "uuid",
        "created",
        "modified",
    ]
    list_display_links = ["name"]
    list_filter = ["type", "is_active", "include_on_net_worth", "include_on_dashboard", "currencies"]
    search_fields = ["name", "uuid", "iban"]
    fieldsets = [
        ["General information", {"fields": ["name", "parent", "iban", "slug", "type", "icon", "currencies", "accountstring"]}],
        ["Options", {"fields": ["is_active", "include_on_net_worth", "include_on_dashboard", "uuid"]}],
    ]
    readonly_fields = ["slug", "icon", "uuid", "accountstring"]
    filter_horizontal = ["currencies"]


class TransactionInline(admin.TabularInline):
    model = models.Transaction
    extra = 0
    fields = ["account", "amount", "currency"]


@admin.register(models.TransactionJournal)
class TransactionJournalAdmin(admin.ModelAdmin):
    def show_tags(self, obj):
        return " ".join(["#{tag}".format(tag=tag) for tag in obj.tags.all()])

    show_tags.short_description = "Tags"

    list_display = ["pk", "short_description", "payee", "date", "show_tags", "uuid", "created", "modified"]
    list_display_links = ["short_description"]
    list_filter = ["payee", TaggitListFilter]
    date_hierarchy = "date"
    search_fields = ["payee", "short_description", "description", "uuid"]
    fieldsets = [
        ["General information", {"fields": ["short_description", "payee", "date", "description", "tags"]}],
        ["Budget", {"fields": ["budgets"]}],
        ["Options", {"fields": ["uuid"]}],
    ]
    filter_horizontal = ["budgets"]
    readonly_fields = ["uuid"]
    inlines = [TransactionInline]


class BudgetPeriodInline(admin.TabularInline):
    model = models.BudgetPeriod
    extra = 0
    fields = ["start_date", "end_date", "amount", "currency", "available", "used", "created", "modified"]
    readonly_fields = fields


@admin.register(models.Budget)
class BudgetAdmin(admin.ModelAdmin):
    ordering = ["name"]
    list_display = ["pk", "name", "is_active", "auto_budget", "period", "uuid", "created", "modified"]
    list_filter = ["is_active", "auto_budget", "period"]
    list_display_links = ["name"]
    search_fields = ["name", "uuid"]
    inlines = [BudgetPeriodInline]
    readonly_fields = ["uuid"]
    fieldsets = [
        ["General information", {"fields": ["name", "is_active", "amount", "currency", "auto_budget", "period"]}],
        ["Options", {"fields": ["uuid"]}],
    ]
