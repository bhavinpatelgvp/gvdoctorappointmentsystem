from django import forms
from .models import Consultation


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = [
            'chief_complaint', 'symptoms', 'clinical_observations',
            'preliminary_diagnosis', 'final_diagnosis', 'treatment',
            'prescription', 'advice', 'follow_up_date',
            'rest_recommended', 'rest_days', 'referral_required',
            'referral_notes', 'additional_notes',
        ]
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'symptoms': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'clinical_observations': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'preliminary_diagnosis': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'final_diagnosis': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'treatment': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'prescription': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'advice': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'referral_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'additional_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rest_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'rest_recommended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'referral_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
