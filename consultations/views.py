from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from accounts.permissions import doctor_required
from accounts.authorization import (
    require_patient_owner, is_doctor, is_admin, get_doctor_profile,
    doctor_owns_appointment, doctor_owns_consultation,
)
from audit.services import log_action
from appointments.models import Appointment
from .models import Consultation
from .forms import ConsultationForm


@doctor_required
def create(request, appointment_id):
    appt = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor'), pk=appointment_id
    )
    if not doctor_owns_appointment(request.user, appt):
        raise PermissionDenied('Not your appointment.')
    existing = getattr(appt, 'consultation', None)
    if existing:
        return redirect('consultations:detail', pk=existing.pk)

    form = ConsultationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cons = form.save(commit=False)
        cons.appointment = appt
        cons.patient = appt.patient
        cons.doctor = appt.doctor
        cons.consultation_date = timezone.now()
        cons.created_by = request.user
        cons.save()
        appt.status = Appointment.STATUS_COMPLETED
        appt.save(update_fields=['status', 'updated_at'])
        log_action(request.user, 'create', 'consultations', cons.pk, f'Consultation for {appt.patient}', request=request)
        messages.success(request, 'Consultation saved. Appointment marked completed.')
        return redirect('consultations:detail', pk=cons.pk)
    return render(request, 'consultations/form.html', {
        'form': form, 'appointment': appt, 'patient': appt.patient, 'title': 'New Consultation',
    })


@login_required
def detail(request, pk):
    cons = get_object_or_404(
        Consultation.objects.select_related('patient', 'doctor', 'appointment'), pk=pk
    )
    # Doctors and admins may view any consultation (clinical access for medical history).
    # Patients may only view their own.
    if is_doctor(request.user) or is_admin(request.user):
        pass
    else:
        require_patient_owner(request.user, cons.patient)
    return render(request, 'consultations/detail.html', {'consultation': cons})


@doctor_required
def edit(request, pk):
    cons = get_object_or_404(Consultation, pk=pk)
    if not doctor_owns_consultation(request.user, cons):
        raise PermissionDenied('Not your consultation.')
    form = ConsultationForm(request.POST or None, instance=cons)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Consultation updated.')
        return redirect('consultations:detail', pk=pk)
    return render(request, 'consultations/form.html', {
        'form': form, 'appointment': cons.appointment, 'patient': cons.patient,
        'title': 'Edit Consultation', 'consultation': cons,
    })
