# Generated by Django 4.0.1 on 2022-01-16 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinapp', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchase',
            old_name='hall_size',
            new_name='count',
        ),
        migrations.AddField(
            model_name='filmsession',
            name='hall_size',
            field=models.IntegerField(default=10),
        ),
    ]
