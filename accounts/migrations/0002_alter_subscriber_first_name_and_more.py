# Generated by Django 5.1.4 on 2025-01-06 00:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriber',
            name='first_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='last_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='phone',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]