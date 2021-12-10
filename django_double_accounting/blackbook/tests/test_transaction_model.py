from django.test import TestCase

from blackbook.models import Account, Transaction, TransactionJournal


class TransactionTest(TestCase):
    def testTransactionCreation(self):
        transactions_to_create = [
            {"account": "Assets:Argenta:Zichtrekening:Bernard", "amount": -10, "currency": "EUR"},
            {"account": "Expenses:Eten:Boodschappen:Colruyt", "amount": 5, "currency": "EUR"},
            {"account": "Expenses:GSM", "amount": 5, "currency": "EUR"},
        ]

        journal_entry = TransactionJournal.create(short_description="Eten", payee="Colruyt", transactions=transactions_to_create)

        self.assertEqual(journal_entry.transactions.count(), 3)

    def testTransactionCreationMissingInput(self):
        transactions_to_create = [
            {"account": "Assets:Argenta:Zichtrekening:Bernard", "amount": -10, "currency": "EUR"},
            {"account": "Expenses:Eten:Boodschappen:Colruyt", "amount": 5, "currency": "EUR"},
            {"account": "Expenses:GSM", "amount": "", "currency": "EUR"},
        ]

        journal_entry = TransactionJournal.create(short_description="Eten", payee="Colruyt", transactions=transactions_to_create)

        self.assertEqual(journal_entry.transactions.count(), 3)
        self.assertEqual(journal_entry.transactions.get(account__accountstring="Expenses:GSM").amount, 5)
