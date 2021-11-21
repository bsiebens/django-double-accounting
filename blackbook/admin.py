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


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = "Name"

    list_display = ["id", "get_full_name", "user", "default_currency"]
    list_display_links = ["get_full_name"]
    ordering = ["user"]
    search_fields = ["user__first_name", "user__last_name", "user__username"]
    raw_id_fields = ["user", "default_currency"]
    list_filter = ["default_currency"]
    fieldsets = [["General information", {"fields": ["user", "default_currency", "created", "modified"]}]]
    readonly_fields = ["created", "modified"]
