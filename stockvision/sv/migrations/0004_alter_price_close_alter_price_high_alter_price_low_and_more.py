# Generated by Django 5.1.2 on 2024-11-10 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sv', '0003_alter_price_options_rename_close_price_price_close_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='price',
            name='close',
            field=models.DecimalField(decimal_places=4, default=0.0, max_digits=14),
        ),
        migrations.AlterField(
            model_name='price',
            name='high',
            field=models.DecimalField(decimal_places=4, default=0.0, max_digits=14),
        ),
        migrations.AlterField(
            model_name='price',
            name='low',
            field=models.DecimalField(decimal_places=4, default=0.0, max_digits=14),
        ),
        migrations.AlterField(
            model_name='price',
            name='open',
            field=models.DecimalField(decimal_places=4, default=0.0, max_digits=14),
        ),
    ]
