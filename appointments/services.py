"""Appointment slot generation and booking rules."""
from datetime import datetime, timedelta, time as time_cls, date as date_cls

from django.db.models import Q

from doctors.models import Doctor, DoctorSchedule, DoctorLeave
from appointments.models import Appointment


ACTIVE_STATUSES = [
    Appointment.STATUS_REQUESTED,
    Appointment.STATUS_CONFIRMED,
    Appointment.STATUS_IN_CONSULTATION,
]


def generate_slots(doctor, on_date):
    """
    Return list of dicts: {time, label, available}
    based on DoctorSchedule, breaks, leave, and existing bookings.
    """
    if doctor.status != 'Active' or doctor.availability != 'Available':
        return []

    if DoctorLeave.objects.filter(doctor=doctor, start_date__lte=on_date, end_date__gte=on_date).exists():
        return []

    weekday = on_date.weekday()
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor, day_of_week=weekday, is_active=True
    ).order_by('start_time')
    if not schedules.exists():
        return []

    booked = set(
        Appointment.objects.filter(
            doctor=doctor, appointment_date=on_date, status__in=ACTIVE_STATUSES,
        ).values_list('appointment_time', flat=True)
    )

    day_count = Appointment.objects.filter(
        doctor=doctor, appointment_date=on_date, status__in=ACTIVE_STATUSES,
    ).count()

    slots = []
    for sched in schedules:
        duration = timedelta(minutes=sched.slot_duration_minutes or 15)
        cursor = datetime.combine(on_date, sched.start_time)
        end_dt = datetime.combine(on_date, sched.end_time)
        while cursor + duration <= end_dt:
            t = cursor.time()
            # skip break
            in_break = False
            if sched.break_start and sched.break_end:
                if sched.break_start <= t < sched.break_end:
                    in_break = True
            available = (
                not in_break
                and t not in booked
                and day_count < (sched.max_patients_per_day or 999)
                and (on_date > date_cls.today() or (
                    on_date == date_cls.today() and t > datetime.now().time()
                ))
            )
            if not in_break:
                slots.append({
                    'time': t,
                    'label': t.strftime('%H:%M'),
                    'available': available and t not in booked,
                    'booked': t in booked,
                })
                if t in booked:
                    # still count toward max already
                    pass
            cursor += duration
    return slots


def search_doctors(medical_system=None, specialization=None, on_date=None):
    qs = Doctor.objects.filter(status='Active', availability='Available').select_related(
        'specialization', 'medical_system', 'department'
    )
    if medical_system:
        qs = qs.filter(medical_system_id=medical_system)
    if specialization:
        qs = qs.filter(specialization_id=specialization)
    if on_date:
        weekday = on_date.weekday()
        qs = qs.filter(schedules__day_of_week=weekday, schedules__is_active=True).distinct()
        qs = qs.exclude(leaves__start_date__lte=on_date, leaves__end_date__gte=on_date)
    return qs
