# Generated by Django 4.0 on 2021-12-09 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0023_budget_amount_budget_currency_budgetperiod_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactionjournal',
            name='budget',
            field=models.ManyToManyField(to='blackbook.Budget'),
        ),
    ]
