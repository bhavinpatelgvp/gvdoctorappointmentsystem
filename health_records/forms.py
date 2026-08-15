from django import forms
from .models import (
    HealthCheckup, CBCReport, RBSReport, BloodPressureReport,
    LipidProfileReport, ClinicalParameter, ClinicalParameterValue,
)


class HealthCheckupForm(forms.ModelForm):
    class Meta:
        model = HealthCheckup
        fields = ['checkup_date', 'notes']
        widgets = {
            'checkup_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class CBCForm(forms.ModelForm):
    class Meta:
        model = CBCReport
        fields = [
            'hemoglobin', 'rbc_count', 'wbc_count', 'platelet_count', 'hematocrit',
            'mcv', 'mch', 'mchc', 'rdw',
            'neutrophils', 'lymphocytes', 'monocytes', 'eosinophils', 'basophils',
            'remarks',
        ]
        widgets = {f: forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}) for f in [
            'hemoglobin', 'rbc_count', 'wbc_count', 'platelet_count', 'hematocrit',
            'mcv', 'mch', 'mchc', 'rdw', 'neutrophils', 'lymphocytes', 'monocytes',
            'eosinophils', 'basophils',
        ]}
        widgets['remarks'] = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})


class RBSForm(forms.ModelForm):
    class Meta:
        model = RBSReport
        fields = ['value', 'unit', 'remarks']
        widgets = {
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BPForm(forms.ModelForm):
    class Meta:
        model = BloodPressureReport
        fields = ['systolic', 'diastolic', 'pulse_rate', 'position', 'measured_at', 'remarks']
        widgets = {
            'systolic': forms.NumberInput(attrs={'class': 'form-control'}),
            'diastolic': forms.NumberInput(attrs={'class': 'form-control'}),
            'pulse_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'measured_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LipidForm(forms.ModelForm):
    class Meta:
        model = LipidProfileReport
        fields = [
            'total_cholesterol', 'hdl', 'ldl', 'triglycerides', 'vldl',
            'cholesterol_hdl_ratio', 'remarks',
        ]
        widgets = {f: forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}) for f in [
            'total_cholesterol', 'hdl', 'ldl', 'triglycerides', 'vldl', 'cholesterol_hdl_ratio',
        ]}
        widgets['remarks'] = forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})


class OtherParamsForm(forms.Form):
    """Dynamic other clinical parameters (height, weight, BMI, etc.)."""
    def __init__(self, *args, parameters=None, **kwargs):
        super().__init__(*args, **kwargs)
        parameters = parameters or ClinicalParameter.objects.filter(category='other', is_active=True)
        for p in parameters:
            self.fields[p.code] = forms.DecimalField(
                required=False, label=f'{p.name} ({p.unit})' if p.unit else p.name,
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            )


class BulkHealthImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.xls'}),
        help_text='CSV or Excel with patient_id, test_date, and clinical columns.',
    )
