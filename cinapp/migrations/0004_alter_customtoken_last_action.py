# Generated by Django 4.0.1 on 2022-01-28 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinapp', '0003_customtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customtoken',
            name='last_action',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
