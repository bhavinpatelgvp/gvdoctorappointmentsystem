from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


def notify(user, notification_type, title, message, link='', send_email=False):
    if not user:
        return None
    n = Notification.objects.create(
        recipient=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )
    if send_email and user.email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            n.email_sent = True
            n.save(update_fields=['email_sent'])
        except Exception:
            pass
    return n


def notify_appointment(appointment, event='booked'):
    titles = {
        'booked': 'Appointment Booked',
        'confirmed': 'Appointment Confirmed',
        'cancelled': 'Appointment Cancelled',
        'reminder': 'Appointment Reminder',
    }
    msg = (
        f"Appointment {appointment.appointment_number} with Dr. {appointment.doctor.name} "
        f"on {appointment.appointment_date} at {appointment.appointment_time} – {event}."
    )
    # Notify patient user if linked
    if appointment.patient.user:
        notify(appointment.patient.user, Notification.TYPE_APPOINTMENT, titles.get(event, 'Appointment'), msg, send_email=True)
    # Notify doctor user if linked
    if appointment.doctor.user:
        notify(appointment.doctor.user, Notification.TYPE_APPOINTMENT, titles.get(event, 'Appointment'), msg)


def notify_certificate(certificate, event='issued'):
    title = f'Medical Certificate {event.title()}'
    msg = (
        f"Certificate {certificate.certificate_number} for {certificate.patient.name} "
        f"has been {event}."
    )
    if certificate.patient.user:
        notify(certificate.patient.user, Notification.TYPE_CERTIFICATE, title, msg, send_email=True)
    # HOD notification for student rest
    if certificate.rest_recommended and certificate.patient.category == 'student':
        try:
            sp = certificate.patient.student_profile
            if sp.department and hasattr(sp.department, 'hod') and sp.department.hod.user:
                hod_msg = (
                    f"Student {certificate.patient.name} ({sp.enrollment_number}) "
                    f"advised rest {certificate.rest_days or ''} day(s) "
                    f"from {certificate.rest_start_date} to {certificate.rest_end_date}."
                )
                notify(
                    sp.department.hod.user, Notification.TYPE_CERTIFICATE,
                    'Student Rest Certificate', hod_msg, send_email=True,
                )
        except Exception:
            pass
