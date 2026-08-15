from django.db import models
from django.conf import settings
from masters.models import Department, Specialization, MedicalSystem


class Doctor(models.Model):
    doctor_id = models.CharField(max_length=30, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_profile',
    )
    name = models.CharField(max_length=150)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True,
    )
    qualification = models.CharField(max_length=200, blank=True)
    medical_system = models.ForeignKey(
        MedicalSystem, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors'
    )
    specialization = models.ForeignKey(
        Specialization, on_delete=models.SET_NULL, null=True, related_name='doctors'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors'
    )
    registration_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    profile_photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    availability = models.CharField(
        max_length=20,
        choices=[('Available', 'Available'), ('Unavailable', 'Unavailable'), ('On Leave', 'On Leave')],
        default='Available',
    )
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        spec = self.specialization.name if self.specialization else 'General'
        return f"Dr. {self.name} ({spec})"


class DoctorSchedule(models.Model):
    """Working schedule for a doctor – supports slot generation."""
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveSmallIntegerField(default=15)
    max_patients_per_day = models.PositiveSmallIntegerField(default=30)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time')
        ordering = ['doctor', 'day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor} – {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class DoctorLeave(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.doctor} leave {self.start_date} to {self.end_date}"
