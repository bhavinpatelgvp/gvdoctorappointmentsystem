# Migration: add timestamps to MedicalSystem

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0002_medicalsystem'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicalsystem',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='medicalsystem',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
