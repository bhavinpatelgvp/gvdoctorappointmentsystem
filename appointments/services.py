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



def ensure_default_schedule(doctor):
    """
    If a doctor has no weekly schedule rows, create Mon–Sat 09:00–17:00
    so they appear with bookable slots for patients.
    """
    if doctor.schedules.exists():
        return
    from datetime import time as time_cls
    for day in range(0, 6):
        DoctorSchedule.objects.get_or_create(
            doctor=doctor,
            day_of_week=day,
            start_time=time_cls(9, 0),
            defaults={
                'end_time': time_cls(17, 0),
                'slot_duration_minutes': 15,
                'max_patients_per_day': 30,
                'break_start': time_cls(13, 0),
                'break_end': time_cls(14, 0),
                'is_active': True,
            },
        )


def search_doctors(medical_system=None, specialization=None, on_date=None):
    """
    List Active + Available doctors.
    When a date is given, exclude doctors on leave that day.
    Doctors without a schedule for that weekday still appear (0 open slots)
    so newly registered doctors are visible to patients.
    """
    qs = Doctor.objects.filter(status='Active', availability='Available').select_related(
        'specialization', 'medical_system', 'department'
    )
    if medical_system:
        qs = qs.filter(medical_system_id=medical_system)
    if specialization:
        qs = qs.filter(specialization_id=specialization)
    if on_date:
        qs = qs.exclude(leaves__start_date__lte=on_date, leaves__end_date__gte=on_date)
    return qs.distinct()
