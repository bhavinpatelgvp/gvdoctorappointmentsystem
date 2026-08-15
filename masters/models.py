from django.db import models
from django.conf import settings


class Department(models.Model):
    department_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
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
        return f"{self.name} ({self.department_code})"


class Programme(models.Model):
    programme_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name='programmes'
    )
    duration_years = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.programme_code})"




class MedicalSystem(models.Model):
    """MBBS / Ayurvedic / Homeopathy etc. – master data, not hard-coded."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Medical System'
        verbose_name_plural = 'Medical Systems'

    def __str__(self):
        return self.name

class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class HOD(models.Model):
    employee_id = models.CharField(max_length=30, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hod_profile',
    )
    name = models.CharField(max_length=150)
    department = models.OneToOneField(
        Department, on_delete=models.PROTECT, related_name='hod'
    )
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Inactive', 'Inactive')],
        default='Active',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'HOD'
        verbose_name_plural = 'HODs'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} – {self.department.name}"
