# Generated by Django 4.0b1 on 2021-11-13 09:50

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CurrencyConversion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('multiplier', models.DecimalField(decimal_places=5, max_digits=20)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('base_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_currency', to='blackbook.currency')),
                ('target_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_currency', to='blackbook.currency')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
    ]
