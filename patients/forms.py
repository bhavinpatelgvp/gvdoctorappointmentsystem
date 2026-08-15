from django import forms
from masters.models import Department, Programme
from patients.models import Patient, StudentProfile, StaffProfile, StaffFamilyProfile


class BS:
    def apply(self):
        for f in self.fields.values():
            if isinstance(f.widget, forms.CheckboxInput):
                f.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(f.widget, (forms.Select, forms.SelectMultiple)):
                f.widget.attrs.setdefault('class', 'form-select')
            else:
                f.widget.attrs.setdefault('class', 'form-control')


class PatientSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Patient ID, name, mobile, email, enrollment, employee ID…'
    }))
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All categories')] + list(Patient.CATEGORY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class DoctorAddPatientForm(forms.Form, BS):
    """Doctor registers a patient at clinic – type-specific fields."""
    patient_type = forms.ChoiceField(
        choices=Patient.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_patient_type'}),
    )
    # Common
    patient_id = forms.CharField(max_length=30)
    name = forms.CharField(max_length=150)
    gender = forms.ChoiceField(choices=[('', '—'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    email = forms.EmailField(required=False)
    mobile = forms.CharField(max_length=15, required=False)
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    blood_group = forms.CharField(max_length=5, required=False)
    emergency_contact = forms.CharField(max_length=15, required=False)
    # Student
    enrollment_number = forms.CharField(max_length=40, required=False)
    programme = forms.ModelChoiceField(queryset=Programme.objects.none(), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.none(), required=False)
    semester = forms.IntegerField(required=False, min_value=1, max_value=12)
    # Staff
    employee_id = forms.CharField(max_length=40, required=False)
    designation = forms.CharField(max_length=100, required=False)
    # Family
    related_staff = forms.ModelChoiceField(queryset=StaffProfile.objects.none(), required=False)
    relationship = forms.ChoiceField(choices=[('', '—')] + list(StaffFamilyProfile.RELATIONSHIP_CHOICES), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['programme'].queryset = Programme.objects.filter(status='Active')
        self.fields['department'].queryset = Department.objects.filter(status='Active')
        self.fields['related_staff'].queryset = StaffProfile.objects.select_related('patient').filter(patient__status='Active')
        self.apply()

    def clean(self):
        cleaned = super().clean()
        ptype = cleaned.get('patient_type')
        pid = cleaned.get('patient_id')
        if pid and Patient.objects.filter(patient_id=pid).exists():
            self.add_error('patient_id', 'A patient with this ID already exists. Search existing patients instead.')
        if ptype == Patient.CATEGORY_STUDENT:
            enr = cleaned.get('enrollment_number')
            if not enr:
                self.add_error('enrollment_number', 'Required for students.')
            elif StudentProfile.objects.filter(enrollment_number=enr).exists():
                self.add_error('enrollment_number', 'Enrollment number already registered.')
        elif ptype == Patient.CATEGORY_STAFF:
            eid = cleaned.get('employee_id')
            if not eid:
                self.add_error('employee_id', 'Required for staff.')
            elif StaffProfile.objects.filter(employee_id=eid).exists():
                self.add_error('employee_id', 'Employee ID already registered.')
        elif ptype == Patient.CATEGORY_STAFF_FAMILY:
            if not cleaned.get('related_staff'):
                self.add_error('related_staff', 'Select related staff member.')
            if not cleaned.get('relationship'):
                self.add_error('relationship', 'Select relationship.')
        return cleaned
