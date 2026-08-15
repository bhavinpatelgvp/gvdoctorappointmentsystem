from django.db import models
from django.conf import settings
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment


class Consultation(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name='consultation', null=True, blank=True
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='consultations')
    consultation_date = models.DateTimeField(db_index=True)
    chief_complaint = models.TextField(blank=True)
    symptoms = models.TextField(blank=True)
    clinical_observations = models.TextField(blank=True)
    preliminary_diagnosis = models.TextField(blank=True)
    final_diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    advice = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    rest_recommended = models.BooleanField(default=False)
    rest_days = models.PositiveSmallIntegerField(null=True, blank=True)
    referral_required = models.BooleanField(default=False)
    referral_notes = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-consultation_date']

    def __str__(self):
        return f"Consultation: {self.patient.name} by {self.doctor} on {self.consultation_date.date()}"
