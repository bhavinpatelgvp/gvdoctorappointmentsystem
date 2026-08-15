from django.db import models
from django.conf import settings
from masters.models import Department, Programme


class Patient(models.Model):
    """Central patient entity – common for appointments, health records, certificates."""
    CATEGORY_STUDENT = 'student'
    CATEGORY_STAFF = 'staff'
    CATEGORY_STAFF_FAMILY = 'staff_family'

    CATEGORY_CHOICES = [
        (CATEGORY_STUDENT, 'Student'),
        (CATEGORY_STAFF, 'University Staff'),
        (CATEGORY_STAFF_FAMILY, 'Staff Family Member'),
    ]

    patient_id = models.CharField(max_length=30, unique=True, db_index=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_profile',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    name = models.CharField(max_length=150, db_index=True)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    mobile = models.CharField(max_length=15, blank=True, db_index=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients_created',
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'mobile']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.patient_id}) – {self.get_category_display()}"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class StudentProfile(models.Model):
    patient = models.OneToOneField(
        Patient, on_delete=models.CASCADE, related_name='student_profile'
    )
    enrollment_number = models.CharField(max_length=40, unique=True, db_index=True)
    programme = models.ForeignKey(
        Programme, on_delete=models.SET_NULL, null=True, blank=True, related_name='students'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students'
    )
    semester = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Student: {self.patient.name} ({self.enrollment_number})"


class StaffProfile(models.Model):
    patient = models.OneToOneField(
        Patient, on_delete=models.CASCADE, related_name='staff_profile'
    )
    employee_id = models.CharField(max_length=40, unique=True, db_index=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_members'
    )
    designation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.patient.name} ({self.employee_id})"


class StaffFamilyProfile(models.Model):
    RELATIONSHIP_CHOICES = [
        ('Spouse', 'Spouse'),
        ('Son', 'Son'),
        ('Daughter', 'Daughter'),
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Other', 'Other authorized dependent'),
    ]
    patient = models.OneToOneField(
        Patient, on_delete=models.CASCADE, related_name='family_profile'
    )
    related_staff = models.ForeignKey(
        StaffProfile, on_delete=models.CASCADE, related_name='family_members'
    )
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES)

    def __str__(self):
        return f"{self.patient.name} ({self.relationship} of {self.related_staff.patient.name})"
