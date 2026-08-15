from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from datetime import date

from accounts.models import Role
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
from health_records.models import HealthCheckup
from certificates.models import MedicalCertificate
from masters.models import Department, HOD
from audit.services import log_action
from accounts.authorization import get_linked_patient


def _user_may_login(user):
    """
    Allow login only when the account and its linked role profile are Active.
    - Django is_active and custom is_active_user must be True
    - Doctor: linked Doctor.status == Active
    - HOD: linked HOD.status == Active
    - Student / Staff / Staff Family: linked Patient.status == Active
    - Admin / Super Admin: only user flags (no extra profile required)
    """
    if not user:
        return False, 'Invalid username or password.'
    if not user.is_active or not getattr(user, 'is_active_user', True):
        return False, 'Your account is inactive. Contact the administrator.'

    role_code = user.role_code if getattr(user, 'role', None) else None

    # Admins / superusers: user flags only
    if user.is_superuser or role_code in (Role.ADMIN, Role.SUPER_ADMIN):
        return True, None

    if role_code == Role.DOCTOR:
        try:
            doctor = user.doctor_profile
        except Exception:
            doctor = None
        if doctor is None:
            return False, 'No doctor profile linked. Contact the administrator.'
        if doctor.status != 'Active':
            return False, 'Your doctor profile is inactive. Contact the administrator.'
        return True, None

    if role_code == Role.HOD:
        try:
            hod = user.hod_profile
        except Exception:
            hod = None
        if hod is None:
            return False, 'No HOD profile linked. Contact the administrator.'
        if hod.status != 'Active':
            return False, 'Your HOD profile is inactive. Contact the administrator.'
        return True, None

    if role_code in (Role.STUDENT, Role.STAFF, Role.STAFF_FAMILY):
        patient = get_linked_patient(user)
        if patient is None:
            return False, 'No patient profile linked. Contact the administrator.'
        if patient.status != 'Active':
            return False, 'Your patient record is inactive. Contact the administrator.'
        return True, None

    # Unknown / missing role – deny
    return False, 'Your account role is not authorized to sign in.'


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.GET.get('session') == 'expired':
        messages.warning(request, 'Your session has expired or your account is inactive. Please sign in again.')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            allowed, reason = _user_may_login(user)
            if not allowed:
                messages.error(request, reason or 'Login not allowed for this account.')
                return render(request, 'accounts/login.html')
            login(request, user)
            log_action(user, 'login', 'accounts', description='User logged in', request=request)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next') or request.POST.get('next') or ''
            if next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('accounts:dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, 'logout', 'accounts', description='User logged out', request=request)
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    user = request.user
    role = user.role_code if user.role else None
    today = date.today()
    context = {'role': role, 'today': today}

    if role in (Role.ADMIN, Role.SUPER_ADMIN) or user.is_superuser:
        context.update({
            'total_students': Patient.objects.filter(category=Patient.CATEGORY_STUDENT, status='Active').count(),
            'total_staff': Patient.objects.filter(category=Patient.CATEGORY_STAFF, status='Active').count(),
            'total_family': Patient.objects.filter(category=Patient.CATEGORY_STAFF_FAMILY, status='Active').count(),
            'total_doctors': Doctor.objects.filter(status='Active').count(),
            'total_hods': HOD.objects.filter(status='Active').count(),
            'total_departments': Department.objects.filter(status='Active').count(),
            'today_appointments': Appointment.objects.filter(appointment_date=today).count(),
            'completed_appointments': Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).count(),
            'pending_appointments': Appointment.objects.filter(
                status__in=[Appointment.STATUS_REQUESTED, Appointment.STATUS_CONFIRMED]
            ).count(),
            'cancelled_appointments': Appointment.objects.filter(status=Appointment.STATUS_CANCELLED).count(),
            'total_checkups': HealthCheckup.objects.count(),
            'recent_certificates': MedicalCertificate.objects.order_by('-created_at')[:5],
            'recent_appointments': Appointment.objects.select_related('patient', 'doctor').order_by('-created_at')[:8],
        })
        return render(request, 'accounts/dashboard_admin.html', context)

    if role == Role.DOCTOR:
        doctor = getattr(user, 'doctor_profile', None)
        if doctor:
            context.update({
                'doctor': doctor,
                'today_appts': Appointment.objects.filter(
                    doctor=doctor, appointment_date=today
                ).exclude(status=Appointment.STATUS_CANCELLED).select_related('patient').order_by('appointment_time'),
                'upcoming': Appointment.objects.filter(
                    doctor=doctor, appointment_date__gt=today,
                    status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_REQUESTED],
                ).select_related('patient').order_by('appointment_date', 'appointment_time')[:10],
                'completed_count': Appointment.objects.filter(
                    doctor=doctor, status=Appointment.STATUS_COMPLETED
                ).count(),
            })
        return render(request, 'accounts/dashboard_doctor.html', context)

    patient = get_linked_patient(user)
    if patient:
        context.update({
            'patient': patient,
            'upcoming_appt': Appointment.objects.filter(
                patient=patient,
                appointment_date__gte=today,
                status__in=[Appointment.STATUS_CONFIRMED, Appointment.STATUS_REQUESTED],
            ).select_related('doctor').order_by('appointment_date', 'appointment_time').first(),
            'appt_history': Appointment.objects.filter(patient=patient).select_related('doctor').order_by('-appointment_date')[:10],
            'latest_checkup': HealthCheckup.objects.filter(patient=patient).order_by('-checkup_date').first(),
            'certificates': MedicalCertificate.objects.filter(patient=patient).order_by('-created_at')[:5],
        })
    return render(request, 'accounts/dashboard_patient.html', context)

def register_view(request):
    """Patient self-registration (student / staff) from the login screen."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    from accounts.forms import PatientRegistrationForm
    form = PatientRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user, patient = form.save()
        log_action(user, 'register', 'accounts', patient.pk, f'Self-registered {patient}', request=request)
        messages.success(
            request,
            f'Registration successful. Your patient ID is {patient.patient_id}. You can sign in now.',
        )
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})

