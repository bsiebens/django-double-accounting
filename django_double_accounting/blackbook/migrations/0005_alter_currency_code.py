# Generated by Django 4.0b1 on 2021-11-13 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackbook', '0004_auto_20211113_1116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='currency',
            name='code',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
