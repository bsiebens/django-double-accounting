# Generated by Django 4.0rc1 on 2021-11-23 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0009_transaction_transactionleg'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='icon',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]