# Generated by Django 4.0rc1 on 2021-11-26 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0012_alter_currency_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='accountstring',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
