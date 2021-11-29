from django.test import TestCase

from blackbook.models import Account


class AccountTest(TestCase):
    def testAccountCreation(self):
        account = Account.objects.create(name="test account", type=Account.AccountType.ASSET_ACCOUNT)

        self.assertEqual(account.icon, "fa-landmark")
        self.assertEqual(account.accountstring, "Assets:test account")

    def testGetOrCreateAccountCreation(self):
        account = Account.get_or_create("Assets:Argenta:Zichtrekening:Bernard")

        self.assertEqual(account.name, "Bernard")
        self.assertEqual(account.parent.name, "Zichtrekening")
        self.assertEqual(account.accountstring, "Assets:Argenta:Zichtrekening:Bernard")
