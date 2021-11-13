from django.test import TestCase
from django.utils import timezone

from datetime import timedelta
from decimal import Decimal

from blackbook.models import Currency, CurrencyConversion


class CurrencyTest(TestCase):
    def testString(self):
        currency = Currency.objects.create(name="Test Currency", code="TEST")

        self.assertEqual(str(currency), "TEST")

    def testCreationWithLowerCaseString(self):
        currency = Currency.objects.create(name="Test Currency", code="test")

        self.assertEqual(str(currency), "TEST")


class CurrencyConversionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.EUR = Currency.objects.create(code="EUR")
        cls.CHF = Currency.objects.create(code="CHF")
        cls.USD = Currency.objects.create(code="USD")

        cls.timestamp = timezone.now()
        cls.EUR_TO_CHF = CurrencyConversion.objects.create(base_currency=cls.EUR, target_currency=cls.CHF, multiplier=2, timestamp=cls.timestamp)

    def testString(self):
        self.assertEqual(str(self.EUR_TO_CHF), "1 EUR = 2 CHF ({timestamp})".format(timestamp=self.timestamp.strftime("%d %b %Y %H:%m")))

    def testConversionWithString(self):
        eur_to_chf = CurrencyConversion.convert(base_currency="EUR", target_currency="CHF", amount=1)
        chf_to_eur = CurrencyConversion.convert(base_currency="CHF", target_currency="EUR", amount=1)

        self.assertEqual(eur_to_chf, 2)
        self.assertEqual(chf_to_eur, 0.5)

    def testConversionWithLowercaseString(self):
        eur_to_chf = CurrencyConversion.convert(base_currency="eur", target_currency="chf", amount=1)
        chf_to_eur = CurrencyConversion.convert(base_currency="chf", target_currency="eur", amount=1)

        self.assertEqual(eur_to_chf, 2)
        self.assertEqual(chf_to_eur, 0.5)

    def testConversionWithSameString(self):
        eur_to_eur = CurrencyConversion.convert(base_currency="EUR", target_currency="EUR", amount=1)

        self.assertEqual(eur_to_eur, 1)

    def testConversionWithStringUnknownCurrency(self):
        usd_to_eur = CurrencyConversion.convert(base_currency="USD", target_currency="EUR", amount=1)
        eur_to_usd = CurrencyConversion.convert(base_currency="EUR", target_currency="USD", amount=1)

        self.assertEqual(usd_to_eur, 1)
        self.assertEqual(eur_to_usd, 1)

    def testConversionWithObjects(self):
        eur_to_chf = CurrencyConversion.convert(base_currency=self.EUR, target_currency=self.CHF, amount=1)
        chf_to_eur = CurrencyConversion.convert(base_currency=self.CHF, target_currency=self.EUR, amount=1)

        self.assertEqual(eur_to_chf, 2)
        self.assertEqual(chf_to_eur, 0.5)

    def testConversionFromConversionObjectWithString(self):
        eur_to_chf = self.EUR_TO_CHF.convert_to(target_currency="CHF", amount=1)

        self.assertEqual(eur_to_chf, 2)

    def testConversionFromConversionObjectWithObject(self):
        eur_to_chf = self.EUR_TO_CHF.convert_to(target_currency=self.CHF, amount=1)

        self.assertEqual(eur_to_chf, 2)

    def testConversionWithNewerReverseConversionTimestamp(self):
        date_yesterday = timezone.now() - timedelta(days=1)

        CurrencyConversion.objects.create(base_currency=self.EUR, target_currency=self.USD, multiplier=2, timestamp=date_yesterday)
        CurrencyConversion.objects.create(base_currency=self.USD, target_currency=self.EUR, multiplier=3)

        eur_to_usd = CurrencyConversion.convert(base_currency="EUR", target_currency="USD", amount=1)

        self.assertAlmostEqual(eur_to_usd, Decimal(0.33), places=2)
