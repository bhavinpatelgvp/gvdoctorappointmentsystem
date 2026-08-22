from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Role
from patients.models import Patient, StudentProfile, StaffProfile
from masters.models import Department, Programme, Specialization, MedicalSystem

User = get_user_model()


class PatientRegistrationForm(forms.Form):
    """Self-registration for students and staff at the login screen."""
    CATEGORY_CHOICES = [
        (Patient.CATEGORY_STUDENT, 'Student'),
        (Patient.CATEGORY_STAFF, 'University Staff'),
    ]

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Choose a username', 'autocomplete': 'username',
    }))
    password = forms.CharField(min_length=6, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Min 6 characters', 'autocomplete': 'new-password',
    }))
    password_confirm = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm password', 'autocomplete': 'new-password',
    }))
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    first_name = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=80, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    mobile = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(
        choices=[('', '—'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'type': 'date', 'class': 'form-control',
    }))
    # Student-specific
    enrollment_number = forms.CharField(max_length=40, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Required for students',
    }))
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(status='Active').order_by('name'),
        required=False,
        empty_label='Select department',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    programme = forms.ModelChoiceField(
        queryset=Programme.objects.filter(status='Active').order_by('name'),
        required=False,
        empty_label='Select programme',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    semester = forms.IntegerField(
        required=False, min_value=1, max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1–8'}),
    )
    # Staff-specific
    employee_id = forms.CharField(max_length=40, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Required for staff',
    }))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password_confirm'):
            if cleaned['password'] != cleaned['password_confirm']:
                self.add_error('password_confirm', 'Passwords do not match.')
        cat = cleaned.get('category')
        if cat == Patient.CATEGORY_STUDENT:
            enr = (cleaned.get('enrollment_number') or '').strip()
            if not enr:
                self.add_error('enrollment_number', 'Enrollment number is required for students.')
            elif StudentProfile.objects.filter(enrollment_number=enr).exists():
                self.add_error('enrollment_number', 'This enrollment number is already registered.')
            if not cleaned.get('department'):
                self.add_error('department', 'Department is required for students.')
            if not cleaned.get('programme'):
                self.add_error('programme', 'Programme is required for students.')
            if not cleaned.get('semester'):
                self.add_error('semester', 'Semester is required for students.')
            # Programme should belong to selected department when both set
            prog = cleaned.get('programme')
            dept = cleaned.get('department')
            if prog and dept and prog.department_id and prog.department_id != dept.pk:
                self.add_error('programme', 'Selected programme does not belong to the chosen department.')
        elif cat == Patient.CATEGORY_STAFF:
            eid = (cleaned.get('employee_id') or '').strip()
            if not eid:
                self.add_error('employee_id', 'Employee ID is required for staff.')
            elif StaffProfile.objects.filter(employee_id=eid).exists():
                self.add_error('employee_id', 'This employee ID is already registered.')
        return cleaned

    def save(self):
        data = self.cleaned_data
        cat = data['category']
        role_code = Role.STUDENT if cat == Patient.CATEGORY_STUDENT else Role.STAFF
        role = Role.objects.get(code=role_code)
        full_name = f"{data['first_name']} {data.get('last_name') or ''}".strip()

        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data.get('email') or '',
                first_name=data['first_name'],
                last_name=data.get('last_name') or '',
                role=role,
                gender=data.get('gender') or '',
                mobile=data.get('mobile') or '',
            )
            # Generate patient_id
            prefix = 'P-STU' if cat == Patient.CATEGORY_STUDENT else 'P-STF'
            count = Patient.objects.filter(category=cat).count() + 1
            patient_id = f'{prefix}-{count:04d}'
            while Patient.objects.filter(patient_id=patient_id).exists():
                count += 1
                patient_id = f'{prefix}-{count:04d}'

            patient = Patient.objects.create(
                patient_id=patient_id,
                user=user,
                category=cat,
                name=full_name,
                gender=data.get('gender') or '',
                date_of_birth=data.get('date_of_birth'),
                email=data.get('email') or '',
                mobile=data.get('mobile') or '',
                status='Active',
                created_by=user,
            )
            if cat == Patient.CATEGORY_STUDENT:
                StudentProfile.objects.create(
                    patient=patient,
                    enrollment_number=data['enrollment_number'].strip(),
                    department=data.get('department'),
                    programme=data.get('programme'),
                    semester=data.get('semester'),
                )
            else:
                StaffProfile.objects.create(
                    patient=patient,
                    employee_id=data['employee_id'].strip(),
                )
        return user, patient


class DoctorRegistrationForm(forms.Form):
    """Self-registration for doctors at the login screen."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Choose a username', 'autocomplete': 'username',
    }))
    password = forms.CharField(min_length=6, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Min 6 characters', 'autocomplete': 'new-password',
    }))
    password_confirm = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm password', 'autocomplete': 'new-password',
    }))
    first_name = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=80, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    mobile = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(
        choices=[('', '—'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    qualification = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'e.g. MBBS, MD',
    }))
    registration_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Medical registration number',
    }))
    experience_years = forms.IntegerField(min_value=0, required=False, initial=0, widget=forms.NumberInput(attrs={
        'class': 'form-control', 'min': 0,
    }))
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.filter(status='Active').order_by('name'),
        required=False,
        empty_label='— Select specialization —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    medical_system = forms.ModelChoiceField(
        queryset=MedicalSystem.objects.filter(status='Active').order_by('name'),
        required=False,
        empty_label='— Select medical system —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Re-bind querysets in case DB was empty at import time
        from masters.models import Specialization, MedicalSystem
        self.fields['specialization'].queryset = Specialization.objects.filter(status='Active').order_by('name')
        self.fields['medical_system'].queryset = MedicalSystem.objects.filter(status='Active').order_by('name')

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password_confirm'):
            if cleaned['password'] != cleaned['password_confirm']:
                self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned

    def save(self):
        from doctors.models import Doctor
        data = self.cleaned_data
        role = Role.objects.get(code=Role.DOCTOR)
        full_name = f"{data['first_name']} {data.get('last_name') or ''}".strip()

        with transaction.atomic():
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data.get('email') or '',
                first_name=data['first_name'],
                last_name=data.get('last_name') or '',
                role=role,
                gender=data.get('gender') or '',
                mobile=data.get('mobile') or '',
            )
            count = Doctor.objects.count() + 1
            doctor_id = f'DOC-{count:04d}'
            while Doctor.objects.filter(doctor_id=doctor_id).exists():
                count += 1
                doctor_id = f'DOC-{count:04d}'
            doctor = Doctor.objects.create(
                doctor_id=doctor_id,
                user=user,
                name=full_name or data['username'],
                gender=data.get('gender') or '',
                qualification=data.get('qualification') or '',
                registration_number=data.get('registration_number') or '',
                email=data.get('email') or '',
                mobile=data.get('mobile') or '',
                experience_years=data.get('experience_years') or 0,
                specialization=data.get('specialization'),
                medical_system=data.get('medical_system'),
                status='Active',
                availability='Available',
            )
            # Default clinic hours so the doctor appears in Find Doctor / Book
            from doctors.models import DoctorSchedule
            from datetime import time as time_cls
            for day in range(0, 6):  # Monday–Saturday
                DoctorSchedule.objects.create(
                    doctor=doctor,
                    day_of_week=day,
                    start_time=time_cls(9, 0),
                    end_time=time_cls(17, 0),
                    slot_duration_minutes=15,
                    max_patients_per_day=30,
                    break_start=time_cls(13, 0),
                    break_end=time_cls(14, 0),
                    is_active=True,
                )
        return user, doctor
