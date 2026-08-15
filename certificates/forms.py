from django import forms
from .models import MedicalCertificate
from patients.models import Patient
from doctors.models import Doctor
from consultations.models import Consultation


class MedicalCertificateForm(forms.ModelForm):
    class Meta:
        model = MedicalCertificate
        fields = [
            'patient', 'consultation', 'consultation_date',
            'medical_advice', 'rest_recommended', 'rest_start_date',
            'rest_end_date', 'rest_days', 'remarks',
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'consultation': forms.Select(attrs={'class': 'form-select'}),
            'consultation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'medical_advice': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'rest_recommended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rest_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rest_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rest_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = Patient.objects.filter(status='Active').order_by('name')
        self.fields['consultation'].queryset = Consultation.objects.select_related('patient').order_by('-consultation_date')[:200]
        self.fields['consultation'].required = False
        if doctor:
            self.fields['consultation'].queryset = Consultation.objects.filter(
                doctor=doctor
            ).select_related('patient').order_by('-consultation_date')[:200]


# Alias used by views
CertificateForm = MedicalCertificateForm
