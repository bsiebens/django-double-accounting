# Generated by Django 4.0 on 2021-12-09 21:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0024_transactionjournal_budget'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transactionjournal',
            old_name='budget',
            new_name='budgets',
        ),
    ]