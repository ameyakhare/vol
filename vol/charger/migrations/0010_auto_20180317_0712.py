# Generated by Django 2.0.3 on 2018-03-17 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charger', '0009_auto_20180317_0636'),
    ]

    operations = [
        migrations.AddField(
            model_name='chargeattempt',
            name='default_kwh',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=6),
        ),
        migrations.AddField(
            model_name='chargeperiod',
            name='kwh',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=6),
        ),
    ]
