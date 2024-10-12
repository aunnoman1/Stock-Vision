# Generated by Django 5.1.1 on 2024-10-09 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sv', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='price',
            name='time',
        ),
        migrations.RemoveField(
            model_name='price',
            name='value',
        ),
        migrations.AddField(
            model_name='price',
            name='close_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='price',
            name='high_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='price',
            name='low_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='price',
            name='open_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
