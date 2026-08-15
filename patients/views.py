from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied

from accounts.permissions import doctor_required
from accounts.authorization import (
    get_linked_patient, require_patient_owner, get_patient_for_user_or_403,
    patient_scoped_qs, is_doctor, is_admin, doctor_can_access_patient,
)
from audit.services import log_action
from appointments.models import Appointment
from health_records.models import HealthCheckup
from certificates.models import MedicalCertificate
from consultations.models import Consultation
from .models import Patient, StudentProfile, StaffProfile, StaffFamilyProfile
from .forms import PatientSearchForm, DoctorAddPatientForm


@login_required
def index(request):
    """
    Global patient search.
    Patients: only themselves. Doctors/admins: searchable list.
    """
    form = PatientSearchForm(request.GET or None)
    own = get_linked_patient(request.user)

    # Strict isolation for patient-role users
    if own and not is_doctor(request.user) and not is_admin(request.user):
        return redirect('patients:detail', patient_id=own.patient_id)

    qs = Patient.objects.filter(status='Active').select_related(
        'student_profile', 'student_profile__department',
        'staff_profile', 'staff_profile__department',
        'family_profile',
    ).order_by('name')

    q = category = ''
    if form.is_valid():
        q = form.cleaned_data.get('q') or ''
        category = form.cleaned_data.get('category') or ''
        if q:
            qs = qs.filter(
                Q(patient_id__icontains=q) | Q(name__icontains=q) |
                Q(mobile__icontains=q) | Q(email__icontains=q) |
                Q(student_profile__enrollment_number__icontains=q) |
                Q(staff_profile__employee_id__icontains=q)
            )
        if category:
            qs = qs.filter(category=category)

    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    return render(request, 'patients/list.html', {
        'page_obj': page, 'form': form, 'q': q, 'category': category,
        'categories': Patient.CATEGORY_CHOICES,
    })


@login_required
def detail(request, patient_id):
    patient = get_object_or_404(
        Patient.objects.select_related(
            'student_profile', 'student_profile__department', 'student_profile__programme',
            'staff_profile', 'staff_profile__department',
            'family_profile', 'family_profile__related_staff',
        ),
        patient_id=patient_id,
    )
    # Mandatory object-level check
    require_patient_owner(request.user, patient)
    if not doctor_can_access_patient(request.user, patient):
        raise PermissionDenied('You do not have permission to access this information.')

    appointments = Appointment.objects.filter(patient=patient).select_related('doctor').order_by('-appointment_date')[:20]
    checkups = HealthCheckup.objects.filter(patient=patient).order_by('-checkup_date')[:20]
    consultations = Consultation.objects.filter(patient=patient).select_related('doctor').order_by('-consultation_date')[:15]
    certificates = MedicalCertificate.objects.filter(patient=patient).order_by('-created_at')[:10]
    return render(request, 'patients/detail.html', {
        'patient': patient,
        'appointments': appointments,
        'checkups': checkups,
        'consultations': consultations,
        'certificates': certificates,
        'show_medical': True,
    })


@login_required
def history(request, patient_id):
    patient = get_patient_for_user_or_403(request.user, patient_id=patient_id)
    checkups = HealthCheckup.objects.filter(patient=patient).prefetch_related(
        'cbc_report', 'rbs_report', 'bp_reports', 'lipid_report', 'parameter_values__parameter',
    ).order_by('-checkup_date')
    consultations = Consultation.objects.filter(patient=patient).select_related('doctor').order_by('-consultation_date')
    appointments = Appointment.objects.filter(patient=patient).select_related('doctor').order_by('-appointment_date')
    certificates = MedicalCertificate.objects.filter(patient=patient).order_by('-created_at')
    return render(request, 'patients/history.html', {
        'patient': patient, 'checkups': checkups, 'consultations': consultations,
        'appointments': appointments, 'certificates': certificates,
    })


@doctor_required
def doctor_add_patient(request):
    pre_q = request.GET.get('q', '').strip()
    existing = []
    if pre_q:
        existing = list(Patient.objects.filter(
            Q(patient_id__icontains=pre_q) | Q(name__icontains=pre_q) |
            Q(mobile__icontains=pre_q) | Q(email__icontains=pre_q) |
            Q(student_profile__enrollment_number__icontains=pre_q) |
            Q(staff_profile__employee_id__icontains=pre_q)
        ).select_related('student_profile', 'staff_profile')[:15])

    form = DoctorAddPatientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            patient = Patient.objects.create(
                patient_id=data['patient_id'],
                category=data['patient_type'],
                name=data['name'],
                gender=data.get('gender') or '',
                date_of_birth=data.get('date_of_birth'),
                email=data.get('email') or '',
                mobile=data.get('mobile') or '',
                address=data.get('address') or '',
                blood_group=data.get('blood_group') or '',
                emergency_contact=data.get('emergency_contact') or '',
                status='Active',
                created_by=request.user,
            )
            if data['patient_type'] == Patient.CATEGORY_STUDENT:
                StudentProfile.objects.create(
                    patient=patient,
                    enrollment_number=data['enrollment_number'],
                    programme=data.get('programme'),
                    department=data.get('department'),
                    semester=data.get('semester'),
                )
            elif data['patient_type'] == Patient.CATEGORY_STAFF:
                StaffProfile.objects.create(
                    patient=patient,
                    employee_id=data['employee_id'],
                    department=data.get('department'),
                    designation=data.get('designation') or '',
                )
            else:
                StaffFamilyProfile.objects.create(
                    patient=patient,
                    related_staff=data['related_staff'],
                    relationship=data['relationship'],
                )
        log_action(request.user, 'create', 'patients', patient.pk, f'Doctor added patient {patient}', request=request)
        messages.success(request, f'Patient {patient.name} ({patient.patient_id}) registered.')
        return redirect('patients:detail', patient_id=patient.patient_id)

    return render(request, 'patients/doctor_add.html', {
        'form': form, 'pre_q': pre_q, 'existing': existing,
    })


@doctor_required
def doctor_edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    # Reuse DoctorAddPatientForm in edit mode is heavy; simple field updates
    if request.method == 'POST':
        patient.name = request.POST.get('name', patient.name)
        patient.mobile = request.POST.get('mobile', patient.mobile)
        patient.email = request.POST.get('email', patient.email)
        patient.address = request.POST.get('address', patient.address)
        patient.blood_group = request.POST.get('blood_group', patient.blood_group)
        patient.emergency_contact = request.POST.get('emergency_contact', patient.emergency_contact)
        patient.save()
        log_action(request.user, 'update', 'patients', patient.pk, f'Updated {patient}', request=request)
        messages.success(request, 'Patient updated.')
        return redirect('patients:detail', patient_id=patient.patient_id)
    return render(request, 'patients/doctor_edit.html', {'patient': patient})


@doctor_required
def doctor_deactivate_patient(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    if request.method == 'POST':
        patient.status = 'Inactive' if patient.status == 'Active' else 'Active'
        patient.save(update_fields=['status'])
        log_action(request.user, 'status_change', 'patients', patient.pk, f'{patient} → {patient.status}', request=request)
        messages.success(request, f'Patient set to {patient.status}.')
    return redirect('patients:detail', patient_id=patient.patient_id)
