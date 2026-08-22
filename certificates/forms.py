from django import forms
from django.db.models import Q
from .models import MedicalCertificate
from patients.models import Patient
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
        # Full querysets – never slice ModelChoiceField querysets (causes "Select a valid choice")
        patients = Patient.objects.filter(status='Active').order_by('name')
        consultations = Consultation.objects.select_related('patient', 'doctor').order_by('-consultation_date')
        if doctor is not None:
            consultations = consultations.filter(doctor=doctor)

        # Always include currently selected values so edit/re-post validates
        if self.instance and self.instance.pk:
            if self.instance.patient_id:
                patients = Patient.objects.filter(
                    Q(pk=self.instance.patient_id) | Q(status='Active')
                ).order_by('name').distinct()
            if self.instance.consultation_id:
                consultations = Consultation.objects.filter(
                    Q(pk=self.instance.consultation_id) | Q(pk__in=consultations.values('pk'))
                ).select_related('patient', 'doctor').order_by('-consultation_date')

        self.fields['patient'].queryset = patients
        self.fields['consultation'].queryset = consultations
        self.fields['consultation'].required = False
        self.fields['rest_days'].required = False
        self.fields['rest_start_date'].required = False
        self.fields['rest_end_date'].required = False


CertificateForm = MedicalCertificateForm
