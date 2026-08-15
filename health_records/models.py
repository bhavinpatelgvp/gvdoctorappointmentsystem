from django.db import models
from django.conf import settings
from patients.models import Patient
from doctors.models import Doctor


class ClinicalParameter(models.Model):
    """Configurable clinical parameters and reference ranges."""
    CATEGORY_CBC = 'cbc'
    CATEGORY_RBS = 'rbs'
    CATEGORY_BP = 'bp'
    CATEGORY_LIPID = 'lipid'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_CBC, 'CBC'),
        (CATEGORY_RBS, 'RBS'),
        (CATEGORY_BP, 'Blood Pressure'),
        (CATEGORY_LIPID, 'Lipid Profile'),
        (CATEGORY_OTHER, 'Other Clinical'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=30, blank=True)
    reference_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gender_specific = models.BooleanField(default=False)
    male_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    male_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    female_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    female_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['category', 'display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_range_for(self, gender=None):
        if self.gender_specific and gender:
            if gender == 'Male' and self.male_min is not None:
                return self.male_min, self.male_max
            if gender == 'Female' and self.female_min is not None:
                return self.female_min, self.female_max
        return self.reference_min, self.reference_max


class HealthCheckup(models.Model):
    """Container for a set of health measurements on a given date."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_checkups')
    doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='health_checkups'
    )
    checkup_date = models.DateField(db_index=True)
    notes = models.TextField(blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        ordering = ['-checkup_date']
        indexes = [models.Index(fields=['patient', 'checkup_date'])]

    def __str__(self):
        return f"Checkup {self.patient.name} on {self.checkup_date}"


class ClinicalParameterValue(models.Model):
    """Extensible storage for any clinical parameter value."""
    STATUS_NORMAL = 'normal'
    STATUS_ABNORMAL = 'abnormal'
    STATUS_UNKNOWN = 'unknown'

    STATUS_CHOICES = [
        (STATUS_NORMAL, 'Within Reference Range'),
        (STATUS_ABNORMAL, 'Outside Configured Reference Range'),
        (STATUS_UNKNOWN, 'Unknown / Not Evaluated'),
    ]

    health_checkup = models.ForeignKey(
        HealthCheckup, on_delete=models.CASCADE, related_name='parameter_values'
    )
    parameter = models.ForeignKey(
        ClinicalParameter, on_delete=models.PROTECT, related_name='values'
    )
    value = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    remarks = models.CharField(max_length=300, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['parameter__display_order']
        unique_together = ('health_checkup', 'parameter')

    def __str__(self):
        return f"{self.parameter.code}: {self.value} {self.unit}"

    def evaluate_status(self, gender=None):
        ref_min, ref_max = self.parameter.get_range_for(gender)
        if ref_min is None and ref_max is None:
            self.status = self.STATUS_UNKNOWN
        elif (ref_min is not None and self.value < ref_min) or (ref_max is not None and self.value > ref_max):
            self.status = self.STATUS_ABNORMAL
        else:
            self.status = self.STATUS_NORMAL
        return self.status


class CBCReport(models.Model):
    """Structured CBC report (also mirrored into ClinicalParameterValue for analytics)."""
    health_checkup = models.OneToOneField(
        HealthCheckup, on_delete=models.CASCADE, related_name='cbc_report'
    )
    hemoglobin = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rbc_count = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    wbc_count = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    platelet_count = models.DecimalField(max_digits=8, decimal_places=0, null=True, blank=True)
    hematocrit = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    mcv = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    mch = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    mchc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rdw = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    neutrophils = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    lymphocytes = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    monocytes = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    eosinophils = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    basophils = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CBC – {self.health_checkup}"


class RBSReport(models.Model):
    health_checkup = models.OneToOneField(
        HealthCheckup, on_delete=models.CASCADE, related_name='rbs_report'
    )
    value = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20, default='mg/dL')
    remarks = models.CharField(max_length=300, blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RBS {self.value} {self.unit} – {self.health_checkup}"


class BloodPressureReport(models.Model):
    health_checkup = models.ForeignKey(
        HealthCheckup, on_delete=models.CASCADE, related_name='bp_reports'
    )
    systolic = models.PositiveSmallIntegerField()
    diastolic = models.PositiveSmallIntegerField()
    pulse_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    position = models.CharField(max_length=30, blank=True)
    measured_at = models.DateTimeField()
    remarks = models.CharField(max_length=300, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-measured_at']

    def __str__(self):
        return f"BP {self.systolic}/{self.diastolic} – {self.health_checkup}"


class LipidProfileReport(models.Model):
    health_checkup = models.OneToOneField(
        HealthCheckup, on_delete=models.CASCADE, related_name='lipid_report'
    )
    total_cholesterol = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    hdl = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ldl = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    triglycerides = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    vldl = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cholesterol_hdl_ratio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lipid – {self.health_checkup}"


class BulkImportLog(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_PARTIAL = 'partial'

    import_type = models.CharField(max_length=50)
    file_name = models.CharField(max_length=255)
    total_records = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default=STATUS_PENDING)
    error_report = models.FileField(upload_to='imports/errors/', blank=True, null=True)
    summary = models.TextField(blank=True)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.import_type} – {self.file_name} ({self.status})"
