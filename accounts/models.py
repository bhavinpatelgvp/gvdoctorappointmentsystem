from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """System roles for RBAC."""
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    STUDENT = 'student'
    STAFF = 'staff'
    STAFF_FAMILY = 'staff_family'
    HOD = 'hod'
    SUPER_ADMIN = 'super_admin'

    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (DOCTOR, 'Doctor'),
        (STUDENT, 'Student'),
        (STAFF, 'Staff'),
        (STAFF_FAMILY, 'Staff Family Member'),
        (HOD, 'HOD'),
        (SUPER_ADMIN, 'Super Administrator'),
    ]

    code = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model with role support."""
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users'
    )
    mobile = models.CharField(max_length=15, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True,
    )
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def role_code(self):
        return self.role.code if self.role else None

    def has_role(self, *codes):
        return self.role and self.role.code in codes

    def is_admin_user(self):
        return self.has_role(Role.ADMIN, Role.SUPER_ADMIN)

    def is_doctor_user(self):
        if self.has_role(Role.DOCTOR, Role.ADMIN, Role.SUPER_ADMIN):
            return True
        try:
            return self.doctor_profile is not None
        except Exception:
            return False

    def is_patient_user(self):
        return self.has_role(Role.STUDENT, Role.STAFF, Role.STAFF_FAMILY)
