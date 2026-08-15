# Migration: link Specialization to MedicalSystem

from django.db import migrations, models
import django.db.models.deletion


def create_default_medical_system(apps, schema_editor):
    MedicalSystem = apps.get_model('masters', 'MedicalSystem')
    if not MedicalSystem.objects.exists():
        MedicalSystem.objects.create(
            code='GENERAL',
            name='General',
            description='Default system for existing specializations',
            status='Active',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('masters', '0003_medical_system_timestamps'),
    ]

    operations = [
        migrations.RunPython(create_default_medical_system, reverse_code=migrations.RunPython.noop),
        migrations.AddField(
            model_name='specialization',
            name='medical_system',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='specializations',
                to='masters.medicalsystem',
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='specialization',
            unique_together={('medical_system', 'name')},
        ),
    ]
