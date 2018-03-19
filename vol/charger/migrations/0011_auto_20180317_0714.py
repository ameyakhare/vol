# Generated by Django 2.0.3 on 2018-03-17 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charger', '0010_auto_20180317_0712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chargeattempt',
            name='default_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
        migrations.AlterField(
            model_name='chargeperiod',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
    ]