from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Role
from patients.models import Patient, StudentProfile, StaffProfile
from masters.models import Department, Programme

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
                )
            else:
                StaffProfile.objects.create(
                    patient=patient,
                    employee_id=data['employee_id'].strip(),
                )
        return user, patient
