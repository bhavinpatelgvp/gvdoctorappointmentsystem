from django.db import models
from django.conf import settings
from patients.models import Patient
from doctors.models import Doctor
from consultations.models import Consultation


class MedicalCertificate(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_ISSUED = 'issued'
    STATUS_SENT = 'sent'
    STATUS_VERIFIED = 'verified'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ISSUED, 'Issued'),
        (STATUS_SENT, 'Sent'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    certificate_number = models.CharField(max_length=40, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='certificates')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='certificates')
    consultation = models.ForeignKey(
        Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificates'
    )
    consultation_date = models.DateField()
    medical_advice = models.TextField(blank=True)
    rest_recommended = models.BooleanField(default=False)
    rest_start_date = models.DateField(null=True, blank=True)
    rest_end_date = models.DateField(null=True, blank=True)
    rest_days = models.PositiveSmallIntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    pdf_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.certificate_number} – {self.patient.name}"
