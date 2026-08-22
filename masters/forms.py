from django import forms
from django.forms import inlineformset_factory
from .models import Department, Programme, Specialization, HOD, MedicalSystem
from doctors.models import Doctor, DoctorSchedule
from patients.models import Patient, StudentProfile, StaffProfile, StaffFamilyProfile


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
            elif isinstance(w, forms.FileInput):
                w.attrs.setdefault('class', 'form-control')
            else:
                w.attrs.setdefault('class', 'form-control')


# ── Department ──────────────────────────────────────────────
class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ['department_code', 'name', 'email', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


# ── Programme ───────────────────────────────────────────────
class ProgrammeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Programme
        fields = ['programme_code', 'name', 'department', 'duration_years', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(status='Active')
        self._apply_bootstrap()


# ── Specialization ──────────────────────────────────────────
class SpecializationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Specialization
        fields = ['code', 'name', 'description', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


# ── HOD ─────────────────────────────────────────────────────
class HODForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = HOD
        fields = ['employee_id', 'name', 'department', 'email', 'mobile', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(status='Active')
        self._apply_bootstrap()


# ── Doctor ──────────────────────────────────────────────────
class DoctorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            'doctor_id', 'name', 'gender', 'qualification', 'medical_system', 'specialization',
            'registration_number', 'email', 'mobile',
            'experience_years', 'availability', 'status', 'profile_photo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialization'].queryset = Specialization.objects.filter(status='Active')
        self.fields['specialization'].required = False
        if 'medical_system' in self.fields:
            self.fields['medical_system'].queryset = MedicalSystem.objects.filter(status='Active')
            self.fields['medical_system'].required = False
        self.fields['profile_photo'].required = False
        # Keep full availability choices; empty not allowed (has default)
        self._apply_bootstrap()


class DoctorScheduleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = [
            'day_of_week', 'start_time', 'end_time', 'slot_duration_minutes',
            'max_patients_per_day', 'break_start', 'break_end', 'is_active',
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'break_start': forms.TimeInput(attrs={'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


DoctorScheduleFormSet = inlineformset_factory(
    Doctor, DoctorSchedule, form=DoctorScheduleForm,
    extra=1, can_delete=True, min_num=0,
)


# ── Student ─────────────────────────────────────────────────
class StudentForm(BootstrapFormMixin, forms.ModelForm):
    """Combined patient + student profile form for admin master."""
    enrollment_number = forms.CharField(max_length=40)
    programme = forms.ModelChoiceField(queryset=Programme.objects.none(), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.none(), required=False)
    semester = forms.IntegerField(min_value=1, max_value=12, required=False)

    class Meta:
        model = Patient
        fields = [
            'patient_id', 'name', 'gender', 'date_of_birth', 'email', 'mobile',
            'address', 'emergency_contact', 'blood_group', 'status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['programme'].queryset = Programme.objects.filter(status='Active')
        self.fields['department'].queryset = Department.objects.filter(status='Active')
        if self.instance and self.instance.pk:
            try:
                sp = self.instance.student_profile
                self.fields['enrollment_number'].initial = sp.enrollment_number
                self.fields['programme'].initial = sp.programme_id
                self.fields['department'].initial = sp.department_id
                self.fields['semester'].initial = sp.semester
            except StudentProfile.DoesNotExist:
                pass
        self._apply_bootstrap()


class StudentImportForm(forms.Form):
    file = forms.FileField(
        label='Excel/CSV file',
        help_text='Upload .xlsx or .csv with student master columns.',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.xls'}),
    )


# ── Staff ───────────────────────────────────────────────────
class StaffForm(BootstrapFormMixin, forms.ModelForm):
    employee_id = forms.CharField(max_length=40)
    department = forms.ModelChoiceField(queryset=Department.objects.none(), required=False)
    designation = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Patient
        fields = [
            'patient_id', 'name', 'gender', 'date_of_birth', 'email', 'mobile',
            'blood_group', 'status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(status='Active')
        if self.instance and self.instance.pk:
            try:
                sp = self.instance.staff_profile
                self.fields['employee_id'].initial = sp.employee_id
                self.fields['department'].initial = sp.department_id
                self.fields['designation'].initial = sp.designation
            except StaffProfile.DoesNotExist:
                pass
        self._apply_bootstrap()


# ── Staff Family ────────────────────────────────────────────
class StaffFamilyForm(BootstrapFormMixin, forms.ModelForm):
    related_staff = forms.ModelChoiceField(
        queryset=StaffProfile.objects.none(),
        label='Related staff member',
    )
    relationship = forms.ChoiceField(choices=StaffFamilyProfile.RELATIONSHIP_CHOICES)

    class Meta:
        model = Patient
        fields = [
            'patient_id', 'name', 'gender', 'date_of_birth', 'email', 'mobile',
            'address', 'blood_group', 'status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_staff'].queryset = StaffProfile.objects.select_related('patient').filter(
            patient__status='Active'
        )
        if self.instance and self.instance.pk:
            try:
                fp = self.instance.family_profile
                self.fields['related_staff'].initial = fp.related_staff_id
                self.fields['relationship'].initial = fp.relationship
            except StaffFamilyProfile.DoesNotExist:
                pass
        self._apply_bootstrap()


class MedicalSystemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MedicalSystem
        fields = ['code', 'name', 'description', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
