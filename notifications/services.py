"""
Notification + email helpers.
SMTP credentials must come from environment / settings — never hard-coded.
"""
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

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
    if send_email and getattr(user, 'email', None):
        if send_plain_email(user.email, title, message):
            n.email_sent = True
            n.save(update_fields=['email_sent'])
    return n


def send_plain_email(to_email, subject, message):
    if not to_email:
        return False
    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return bool(sent)
    except Exception as exc:
        # Log to console so DEMO/console backend issues are visible
        print(f'[EMAIL ERROR] to={to_email} subject={subject!r}: {exc}')
        return False


def send_certificate_email(to_email, subject, body, certificate=None):
    """Send certificate email; attach PDF when present on the certificate."""
    if not to_email:
        return False
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        if certificate is not None:
            pdf = getattr(certificate, 'pdf_file', None)
            if pdf:
                try:
                    pdf.open('rb')
                    data = pdf.read()
                    pdf.close()
                    if data:
                        email.attach(
                            f'{certificate.certificate_number}.pdf',
                            data,
                            'application/pdf',
                        )
                except Exception as exc:
                    print(f'[EMAIL PDF ATTACH ERROR] {exc}')
        email.send(fail_silently=False)
        print(f'[EMAIL SENT] to={to_email} subject={subject!r}')
        return True
    except Exception as exc:
        print(f'[EMAIL ERROR] to={to_email} subject={subject!r}: {exc}')
        return False


def notify_appointment(appointment, event='booked'):
    titles = {
        'booked': 'Appointment Booked',
        'confirmed': 'Appointment Confirmed',
        'cancelled': 'Appointment Cancelled',
        'reminder': 'Appointment Reminder',
    }
    title = titles.get(event, 'Appointment')
    msg = (
        f"Appointment {appointment.appointment_number} with Dr. {appointment.doctor.name} "
        f"on {appointment.appointment_date} at {appointment.appointment_time} – {event}."
    )
    if appointment.patient.user:
        notify(appointment.patient.user, Notification.TYPE_APPOINTMENT, title, msg, send_email=True)
    patient_email = (appointment.patient.email or '').strip()
    user_email = ''
    if appointment.patient.user:
        user_email = (appointment.patient.user.email or '').strip()
    if patient_email and patient_email.lower() != user_email.lower():
        send_plain_email(patient_email, title, msg)
    if appointment.doctor.user:
        notify(appointment.doctor.user, Notification.TYPE_APPOINTMENT, title, msg)


def resolve_patient_department(patient):
    """Department for student, staff, or staff-family patient."""
    try:
        if patient.category == 'student':
            sp = getattr(patient, 'student_profile', None)
            if sp is None:
                return None
            return sp.department
        if patient.category == 'staff':
            sp = getattr(patient, 'staff_profile', None)
            if sp is None:
                return None
            return sp.department
        if patient.category == 'staff_family':
            fp = getattr(patient, 'family_profile', None)
            if fp is None or not fp.related_staff:
                return None
            return fp.related_staff.department
    except ObjectDoesNotExist:
        return None
    except Exception as exc:
        print(f'[DEPT RESOLVE ERROR] {exc}')
        return None
    return None


def resolve_hod(department):
    """Safe HOD lookup for a department (OneToOne related_name='hod')."""
    if not department:
        return None
    try:
        return department.hod
    except ObjectDoesNotExist:
        return None
    except Exception:
        return None


def notify_certificate(certificate, event='issued'):
    """
    Send rest / medical certificate emails to:
      1. Patient email (Patient.email + linked User.email)
      2. Concerned department HOD email (when rest_recommended)
         – HOD.email, HOD.user.email, Department.email

    Returns list of (role, email) successfully sent.
    """
    from certificates.models import MedicalCertificate

    # Refresh so pdf_file is current after save
    try:
        certificate.refresh_from_db()
    except Exception:
        pass

    patient = certificate.patient
    doctor_name = certificate.doctor.name if certificate.doctor_id else 'Doctor'

    rest_block = ''
    if certificate.rest_recommended:
        rest_block = (
            f"\n\nREST ADVISED\n"
            f"Days: {certificate.rest_days or '—'}\n"
            f"From: {certificate.rest_start_date or '—'}\n"
            f"To:   {certificate.rest_end_date or '—'}\n"
        )

    subject = f"[Gujarat Vidyapith] Medical Certificate {certificate.certificate_number} – {event.title()}"
    patient_body = (
        f"Dear {patient.name},\n\n"
        f"Your medical certificate has been {event}.\n\n"
        f"Certificate No.: {certificate.certificate_number}\n"
        f"Patient ID:      {patient.patient_id}\n"
        f"Doctor:          Dr. {doctor_name}\n"
        f"Date:            {certificate.consultation_date or '—'}\n"
        f"Medical advice:  {certificate.medical_advice or '—'}\n"
        f"{rest_block}\n"
        f"— Gujarat Vidyapith Health Centre (system notification)\n"
    )

    emailed = []

    # -------- Patient --------
    patient_emails = set()
    if (patient.email or '').strip():
        patient_emails.add(patient.email.strip().lower())
    if patient.user_id:
        try:
            uemail = (patient.user.email or '').strip()
            if uemail:
                patient_emails.add(uemail.lower())
        except Exception:
            pass

    for addr in patient_emails:
        if send_certificate_email(addr, subject, patient_body, certificate):
            emailed.append(('patient', addr))

    if patient.user_id:
        try:
            notify(
                patient.user, Notification.TYPE_CERTIFICATE, subject, patient_body,
                send_email=False,
            )
        except Exception:
            pass

    # -------- HOD (rest certificates) --------
    if certificate.rest_recommended:
        department = resolve_patient_department(patient)
        hod = resolve_hod(department)
        enrollment = ''
        try:
            if patient.category == 'student' and hasattr(patient, 'student_profile') and patient.student_profile:
                enrollment = patient.student_profile.enrollment_number or ''
        except Exception:
            pass

        dept_name = department.name if department else '—'
        hod_subject = (
            f"[Gujarat Vidyapith] Rest Certificate – {patient.name} ({dept_name})"
        )
        hod_body = (
            f"Dear {hod.name if hod else 'HOD'},\n\n"
            f"A medical rest certificate has been issued for a student/staff member "
            f"of your department.\n\n"
            f"Patient:         {patient.name}\n"
            f"Patient ID:      {patient.patient_id}\n"
            f"Enrollment/ID:   {enrollment or '—'}\n"
            f"Category:        {patient.get_category_display()}\n"
            f"Department:      {dept_name}\n"
            f"Certificate No.: {certificate.certificate_number}\n"
            f"Doctor:          Dr. {doctor_name}\n"
            f"Rest from:       {certificate.rest_start_date or '—'}\n"
            f"Rest to:         {certificate.rest_end_date or '—'}\n"
            f"Rest days:       {certificate.rest_days or '—'}\n"
            f"Advice:          {certificate.medical_advice or '—'}\n\n"
            f"Please treat this as an institutional health notification.\n"
            f"— Gujarat Vidyapith Health Centre (system notification)\n"
        )

        hod_emails = set()
        if hod:
            if (hod.email or '').strip():
                hod_emails.add(hod.email.strip().lower())
            if hod.user_id:
                try:
                    he = (hod.user.email or '').strip()
                    if he:
                        hod_emails.add(he.lower())
                except Exception:
                    pass
        if department and (department.email or '').strip():
            hod_emails.add(department.email.strip().lower())

        for addr in hod_emails:
            if send_certificate_email(addr, hod_subject, hod_body, certificate):
                emailed.append(('hod', addr))

        if hod and hod.user_id:
            try:
                notify(
                    hod.user, Notification.TYPE_CERTIFICATE, hod_subject, hod_body,
                    send_email=False,
                )
            except Exception:
                pass

        if not hod_emails:
            print(
                f'[EMAIL WARN] No HOD/department email for patient {patient.patient_id} '
                f'dept={dept_name} rest certificate {certificate.certificate_number}'
            )

    if not patient_emails:
        print(
            f'[EMAIL WARN] No patient email for {patient.patient_id} '
            f'certificate {certificate.certificate_number}'
        )

    # Update status when any mail went out
    if emailed:
        try:
            if certificate.status in (
                MedicalCertificate.STATUS_DRAFT,
                MedicalCertificate.STATUS_ISSUED,
            ):
                certificate.status = MedicalCertificate.STATUS_SENT
                certificate.save(update_fields=['status', 'updated_at'])
        except Exception as exc:
            print(f'[CERT STATUS ERROR] {exc}')

    return emailed
