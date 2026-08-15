from django.db import models
from django.conf import settings
from patients.models import Patient
from doctors.models import Doctor


class Appointment(models.Model):
    STATUS_REQUESTED = 'requested'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_IN_CONSULTATION = 'in_consultation'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_RESCHEDULED = 'rescheduled'
    STATUS_NO_SHOW = 'no_show'

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_IN_CONSULTATION, 'In Consultation'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_RESCHEDULED, 'Rescheduled'),
        (STATUS_NO_SHOW, 'No-show'),
    ]

    appointment_number = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField(db_index=True)
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REQUESTED, db_index=True)
    reason = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)
    cancelled_reason = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['doctor', 'appointment_date', 'appointment_time']),
            models.Index(fields=['patient', 'appointment_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=models.Q(status__in=['requested', 'confirmed', 'in_consultation']),
                name='unique_active_doctor_slot',
            )
        ]

    def __str__(self):
        return f"{self.appointment_number}: {self.patient.name} with {self.doctor} on {self.appointment_date}"
