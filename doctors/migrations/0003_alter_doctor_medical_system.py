# Migration: make Doctor.medical_system non-nullable with PROTECT

from django.db import migrations, models
import django.db.models.deletion


def set_default_medical_system(apps, schema_editor):
    Doctor = apps.get_model('doctors', 'Doctor')
    MedicalSystem = apps.get_model('masters', 'MedicalSystem')
    default_system = MedicalSystem.objects.first()
    if default_system:
        Doctor.objects.filter(medical_system__isnull=True).update(medical_system=default_system)


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0002_doctor_medical_system'),
        ('masters', '0005_alter_specialization_options_and_more'),
    ]

    operations = [
        migrations.RunPython(set_default_medical_system, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='doctor',
            name='medical_system',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='doctors',
                to='masters.medicalsystem',
            ),
        ),
    ]
