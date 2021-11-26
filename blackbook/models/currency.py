from django.db import models
from django.db.models import Q, base
from django.utils import timezone

from decimal import Decimal


class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=250, blank=True, null=True)
    default_currency = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper()

        super(Currency, self).save(*args, **kwargs)


class CurrencyConversion(models.Model):
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="base_currency")
    target_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="target_currency")
    multiplier = models.DecimalField(max_digits=20, decimal_places=5)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return "1 {i.base_currency} = {i.multiplier} {i.target_currency} ({timestamp})".format(
            i=self, timestamp=self.timestamp.strftime("%d %b %Y %H:%m")
        )

    @classmethod
    def convert(cls, base_currency, target_currency, amount):
        conversion_object = None
        multiplier = 1

        base_currency = base_currency.upper() if type(base_currency) == str else base_currency
        target_currency = target_currency.upper() if type(target_currency) == str else target_currency

        if base_currency == target_currency:
            return amount

        try:
            conversion_object = (
                cls.objects.filter(
                    Q(base_currency__code=base_currency, target_currency__code=target_currency)
                    | Q(base_currency__code=target_currency, target_currency__code=base_currency)
                )
                .select_related()
                .latest("timestamp")
            )

            if conversion_object.base_currency.code == str(base_currency):
                multiplier = conversion_object.multiplier
            else:
                multiplier = 1 / conversion_object.multiplier

        except cls.DoesNotExist:
            pass

        return Decimal(amount) * multiplier

    def convert_to(self, target_currency, amount=1):
        return self.__class__.convert(base_currency=self.base_currency, target_currency=target_currency, amount=amount)
