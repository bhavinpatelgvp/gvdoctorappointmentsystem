from django import forms
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from doctors.models import Doctor, DoctorSchedule, DoctorLeave
from patients.models import Patient
from .models import Appointment


class AppointmentBookForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(status='Active', availability='Available'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    reason = forms.CharField(max_length=300, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.patient = patient

    def clean_appointment_date(self):
        d = self.cleaned_data['appointment_date']
        if d < date.today():
            raise forms.ValidationError('Cannot book a past date.')
        return d

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        adate = cleaned.get('appointment_date')
        atime = cleaned.get('appointment_time')
        if not (doctor and adate and atime):
            return cleaned

        if doctor.availability != 'Available':
            raise forms.ValidationError('Doctor is not available for booking.')

        # Leave check
        if DoctorLeave.objects.filter(doctor=doctor, start_date__lte=adate, end_date__gte=adate).exists():
            raise forms.ValidationError('Doctor is on leave on the selected date.')

        # Schedule check
        weekday = adate.weekday()  # Mon=0
        schedules = DoctorSchedule.objects.filter(doctor=doctor, day_of_week=weekday, is_active=True)
        if not schedules.exists():
            raise forms.ValidationError('Doctor does not work on the selected day.')
        in_slot = False
        for s in schedules:
            if s.start_time <= atime < s.end_time:
                if s.break_start and s.break_end and s.break_start <= atime < s.break_end:
                    raise forms.ValidationError('Selected time falls in doctor break.')
                in_slot = True
                # max patients
                day_count = Appointment.objects.filter(
                    doctor=doctor, appointment_date=adate,
                    status__in=['requested', 'confirmed', 'in_consultation'],
                ).count()
                if day_count >= s.max_patients_per_day:
                    raise forms.ValidationError('Maximum patients for this day reached.')
                break
        if not in_slot:
            raise forms.ValidationError('Selected time is outside doctor working hours.')

        # Double booking
        if Appointment.objects.filter(
            doctor=doctor, appointment_date=adate, appointment_time=atime,
            status__in=['requested', 'confirmed', 'in_consultation'],
        ).exists():
            raise forms.ValidationError('This slot is already booked.')

        # Patient duplicate same day same doctor
        if self.patient and Appointment.objects.filter(
            patient=self.patient, doctor=doctor, appointment_date=adate,
            status__in=['requested', 'confirmed', 'in_consultation'],
        ).exists():
            raise forms.ValidationError('You already have an active appointment with this doctor on this date.')

        return cleaned


class AppointmentRescheduleForm(forms.Form):
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    reason = forms.CharField(max_length=300, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class AppointmentCancelForm(forms.Form):
    cancelled_reason = forms.CharField(
        max_length=300, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for cancellation'}),
    )
