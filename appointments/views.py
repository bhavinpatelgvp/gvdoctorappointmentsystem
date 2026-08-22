from datetime import date, datetime
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied

from accounts.permissions import doctor_required
from accounts.authorization import (
    get_linked_patient, get_doctor_profile, is_doctor, is_admin, patient_scoped_qs,
    require_patient_owner, doctor_owns_appointment,
)
from audit.services import log_action
from doctors.models import Doctor
from patients.models import Patient
from masters.models import Specialization, MedicalSystem
from notifications.services import notify_appointment
from .models import Appointment
from .forms import AppointmentBookForm, AppointmentRescheduleForm, AppointmentCancelForm
from .services import generate_slots, search_doctors


def _next_appt_number():
    """Unique APTYYYYMMDD#### using max suffix (not count) to avoid seed/gap collisions."""
    import re
    import uuid

    today = date.today().strftime('%Y%m%d')
    prefix = f'APT{today}'
    existing = Appointment.objects.filter(
        appointment_number__startswith=prefix
    ).values_list('appointment_number', flat=True)

    max_seq = 0
    for num in existing:
        m = re.search(r'(\d+)$', num or '')
        if m:
            try:
                max_seq = max(max_seq, int(m.group(1)))
            except ValueError:
                pass

    seq = max_seq + 1
    for _ in range(1000):
        candidate = f'{prefix}{seq:04d}'
        if not Appointment.objects.filter(appointment_number=candidate).exists():
            return candidate
        seq += 1
    return f'{prefix}{uuid.uuid4().hex[:8].upper()}'


def _create_appointment_unique(**kwargs):
    """Create appointment; regenerate number if UNIQUE constraint races."""
    from django.db import IntegrityError

    last_err = None
    for _ in range(8):
        kwargs['appointment_number'] = _next_appt_number()
        try:
            with transaction.atomic():
                return Appointment.objects.create(**kwargs)
        except IntegrityError as exc:
            last_err = exc
            if 'appointment_number' not in str(exc).lower() and 'UNIQUE' not in str(exc):
                raise
            continue
    raise last_err


@login_required
def index(request):
    status = request.GET.get('status', '')
    date_from = request.GET.get('from', '')
    q = request.GET.get('q', '').strip()
    qs = Appointment.objects.select_related(
        'patient', 'doctor', 'doctor__specialization'
    ).all()
    # Mandatory scoping for patients
    qs = patient_scoped_qs(request.user, qs)
    profile = get_doctor_profile(request.user)
    if profile is not None and not is_admin(request.user):
        qs = qs.filter(doctor=profile)
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(appointment_date__gte=date_from)
    if q:
        qs = qs.filter(
            Q(appointment_number__icontains=q) |
            Q(patient__name__icontains=q) |
            Q(patient__patient_id__icontains=q) |
            Q(doctor__name__icontains=q)
        )
    page = Paginator(qs.order_by('-appointment_date', '-appointment_time'), 10).get_page(request.GET.get('page'))
    # Only patients get book/find-doctor affordances
    from accounts.authorization import is_patient_role
    can_book = is_patient_role(request.user)
    return render(request, 'appointments/list.html', {
        'page_obj': page,
        'appointments': page,
        'status': status, 'statuses': Appointment.STATUS_CHOICES,
        'date_from': date_from, 'q': q, 'can_book': can_book,
    })


@login_required
def find_doctor(request):
    """Patient workflow: Medical System → Specialization → Date → Doctors + slots."""
    systems = MedicalSystem.objects.filter(status='Active')
    specs = Specialization.objects.filter(status='Active')
    ms = request.GET.get('medical_system', '')
    spec = request.GET.get('specialization', '')
    date_str = request.GET.get('date', '')
    on_date = None
    doctors = []
    if date_str:
        try:
            on_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date.')
    if request.GET.get('search'):
        from .services import ensure_default_schedule
        doctors = list(search_doctors(
            medical_system=ms or None,
            specialization=spec or None,
            on_date=on_date,
        ))
        # attach slots if date given; ensure schedule so new doctors are bookable
        for d in doctors:
            ensure_default_schedule(d)
            d.available_slots = generate_slots(d, on_date) if on_date else []
            d.open_slot_count = sum(1 for s in d.available_slots if s['available'])
    return render(request, 'appointments/find_doctor.html', {
        'systems': systems, 'specs': specs,
        'ms': ms, 'spec': spec, 'date_str': date_str,
        'doctors': doctors, 'on_date': on_date,
    })


@login_required
def book(request):
    """Book a specific doctor slot – ownership enforced for patients."""
    own = get_linked_patient(request.user)
    patient = own
    if not patient and (is_admin(request.user) or is_doctor(request.user)):
        pid = request.GET.get('patient') or request.POST.get('patient_id')
        if pid:
            patient = Patient.objects.filter(patient_id=pid).first() or Patient.objects.filter(pk=pid).first()

    doctor_id = request.GET.get('doctor') or request.POST.get('doctor')
    date_str = request.GET.get('date') or request.POST.get('appointment_date')
    time_str = request.GET.get('time') or request.POST.get('appointment_time')

    doctor = Doctor.objects.filter(pk=doctor_id, status='Active').first() if doctor_id else None
    on_date = None
    if date_str:
        try:
            on_date = datetime.strptime(str(date_str)[:10], '%Y-%m-%d').date()
        except ValueError:
            on_date = None

    slots = generate_slots(doctor, on_date) if doctor and on_date else []

    if request.method == 'POST':
        if not patient:
            messages.error(request, 'Patient profile required to book.')
            return redirect('appointments:find_doctor')
        # Patients may only book for themselves
        if own and patient.pk != own.pk:
            raise PermissionDenied('You can only book appointments for yourself.')

        form = AppointmentBookForm(request.POST, patient=patient)
        if form.is_valid():
            data = form.cleaned_data
            # Re-validate slot still available
            still = generate_slots(data['doctor'], data['appointment_date'])
            ok = any(s['time'] == data['appointment_time'] and s['available'] for s in still)
            if not ok:
                messages.error(request, 'Selected slot is no longer available.')
            else:
                appt = _create_appointment_unique(
                    patient=patient,
                    doctor=data['doctor'],
                    appointment_date=data['appointment_date'],
                    appointment_time=data['appointment_time'],
                    status=Appointment.STATUS_REQUESTED,
                    reason=data.get('reason') or '',
                    created_by=request.user,
                )
                notify_appointment(appt, 'booked')
                log_action(request.user, 'create', 'appointments', appt.pk, appt.appointment_number, request=request)
                messages.success(request, f'Appointment {appt.appointment_number} booked.')
                return redirect('appointments:detail', pk=appt.pk)
        else:
            for e in form.non_field_errors():
                messages.error(request, e)
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')

    initial = {}
    if doctor:
        initial['doctor'] = doctor.pk
    if on_date:
        initial['appointment_date'] = on_date
    if time_str:
        try:
            initial['appointment_time'] = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            pass
    form = AppointmentBookForm(initial=initial, patient=patient)
    return render(request, 'appointments/book.html', {
        'form': form, 'patient': patient, 'doctor': doctor,
        'slots': slots, 'on_date': on_date,
    })


@login_required
def detail(request, pk):
    appt = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor', 'doctor__specialization'), pk=pk
    )
    # Object-level: patient only own; doctor only own appointments (or admin)
    user = request.user
    if is_admin(user):
        pass
    elif is_doctor(user):
        if not doctor_owns_appointment(user, appt):
            raise PermissionDenied('You can only view your own appointments.')
    else:
        require_patient_owner(user, appt.patient)
    return render(request, 'appointments/detail.html', {'appointment': appt})


@login_required
def cancel(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    user = request.user
    if not is_admin(user) and not is_doctor(user):
        require_patient_owner(user, appt.patient)
    if appt.status in (Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED):
        messages.warning(request, 'This appointment cannot be cancelled.')
        return redirect('appointments:detail', pk=pk)
    form = AppointmentCancelForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appt.status = Appointment.STATUS_CANCELLED
        appt.cancelled_reason = form.cleaned_data.get('cancelled_reason') or ''
        appt.save(update_fields=['status', 'cancelled_reason', 'updated_at'])
        notify_appointment(appt, 'cancelled')
        log_action(request.user, 'cancel', 'appointments', appt.pk, appt.appointment_number, request=request)
        messages.success(request, 'Appointment cancelled.')
        return redirect('appointments:detail', pk=pk)
    return render(request, 'appointments/cancel.html', {'form': form, 'appointment': appt})


@login_required
def reschedule(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if not is_admin(request.user) and not is_doctor(request.user):
        require_patient_owner(request.user, appt.patient)
    if appt.status in (Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED):
        messages.warning(request, 'Cannot reschedule this appointment.')
        return redirect('appointments:detail', pk=pk)
    slots = generate_slots(appt.doctor, appt.appointment_date)
    form = AppointmentRescheduleForm(request.POST or None, initial={
        'appointment_date': appt.appointment_date,
        'appointment_time': appt.appointment_time,
    })
    if request.method == 'POST' and form.is_valid():
        new_date = form.cleaned_data['appointment_date']
        new_time = form.cleaned_data['appointment_time']
        book_form = AppointmentBookForm(data={
            'doctor': appt.doctor_id,
            'appointment_date': new_date,
            'appointment_time': new_time,
            'reason': form.cleaned_data.get('reason') or '',
        }, patient=appt.patient)
        if book_form.is_valid():
            appt.appointment_date = new_date
            appt.appointment_time = new_time
            appt.status = Appointment.STATUS_CONFIRMED
            if form.cleaned_data.get('reason'):
                appt.reason = form.cleaned_data['reason']
            appt.save()
            messages.success(request, 'Appointment rescheduled.')
            return redirect('appointments:detail', pk=pk)
        for err in book_form.non_field_errors():
            messages.error(request, err)
    return render(request, 'appointments/reschedule.html', {
        'form': form, 'appointment': appt, 'slots': slots,
    })


@doctor_required
def confirm(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if not doctor_owns_appointment(request.user, appt):
        raise PermissionDenied('You can only confirm your own appointments.')
    if request.method == 'POST':
        appt.status = Appointment.STATUS_CONFIRMED
        appt.save(update_fields=['status', 'updated_at'])
        notify_appointment(appt, 'confirmed')
        messages.success(request, 'Appointment confirmed.')
    return redirect('appointments:detail', pk=pk)


@doctor_required
def start_consultation(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if not doctor_owns_appointment(request.user, appt):
        raise PermissionDenied('You can only start consultation for your own appointments.')
    appt.status = Appointment.STATUS_IN_CONSULTATION
    appt.save(update_fields=['status', 'updated_at'])
    return redirect('consultations:create', appointment_id=appt.pk)
