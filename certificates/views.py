from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from accounts.permissions import doctor_required
from accounts.authorization import (
    require_patient_owner, patient_scoped_qs, get_doctor_profile, is_admin, is_doctor,
)
from audit.services import log_action
from patients.models import Patient
from consultations.models import Consultation
from notifications.services import notify_certificate
from .models import MedicalCertificate
from .forms import CertificateForm, MedicalCertificateForm
from .pdf_generator import generate_certificate_pdf


def _next_cert_number():
    today = date.today().strftime('%Y%m%d')
    prefix = f'CERT-{today}-'
    last = MedicalCertificate.objects.filter(certificate_number__startswith=prefix).count()
    return f'{prefix}{last + 1:04d}'


@login_required
def index(request):
    q = request.GET.get('q', '').strip()
    qs = MedicalCertificate.objects.select_related('patient', 'doctor').order_by('-created_at')
    qs = patient_scoped_qs(request.user, qs)
    profile = get_doctor_profile(request.user)
    if profile is not None and not is_admin(request.user):
        # Doctor list: certificates they issued (still own-patient for pure patients via scope)
        qs = qs.filter(doctor=profile)
    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(certificate_number__icontains=q) | Q(patient__name__icontains=q) |
            Q(patient__patient_id__icontains=q)
        )
    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    return render(request, 'certificates/list.html', {
        'page_obj': page, 'certificates': page, 'q': q,
    })


@doctor_required
def create(request):
    doctor = get_doctor_profile(request.user)
    patient_id = request.GET.get('patient') or request.POST.get('patient_id')
    consultation_id = request.GET.get('consultation')
    initial = {}
    patient = None
    consultation = None
    if patient_id:
        patient = Patient.objects.filter(patient_id=patient_id).first()
        if patient:
            initial['patient'] = patient.pk
    if consultation_id:
        consultation = Consultation.objects.filter(pk=consultation_id).select_related('patient').first()
        if consultation:
            patient = consultation.patient
            initial['patient'] = patient.pk
            initial['consultation'] = consultation.pk
            initial['consultation_date'] = consultation.consultation_date.date() if consultation.consultation_date else date.today()
            if consultation.rest_recommended:
                initial['rest_recommended'] = True
                initial['rest_days'] = consultation.rest_days
                initial['medical_advice'] = consultation.advice or 'Rest advised'

    form = CertificateForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            cert = form.save(commit=False)
            cert.certificate_number = _next_cert_number()
            cert.doctor = doctor or cert.doctor
            cert.status = MedicalCertificate.STATUS_ISSUED
            cert.issued_at = timezone.now()
            cert.created_by = request.user
            cert.save()
            try:
                pdf_bytes = generate_certificate_pdf(cert)
                cert.pdf_file.save(f'{cert.certificate_number}.pdf', ContentFile(pdf_bytes), save=True)
            except Exception as exc:
                messages.warning(request, f'Certificate saved but PDF failed: {exc}')
            notify_certificate(cert, 'issued')
            log_action(request.user, 'create', 'certificates', cert.pk, cert.certificate_number, request=request)
        messages.success(request, f'Certificate {cert.certificate_number} issued.')
        return redirect('certificates:detail', pk=cert.pk)

    return render(request, 'certificates/form.html', {
        'form': form, 'patient': patient, 'consultation': consultation,
    })


@login_required
def detail(request, pk):
    cert = get_object_or_404(
        MedicalCertificate.objects.select_related('patient', 'doctor', 'consultation'), pk=pk
    )
    require_patient_owner(request.user, cert.patient)
    return render(request, 'certificates/detail.html', {'certificate': cert})


@login_required
def download(request, pk):
    cert = get_object_or_404(MedicalCertificate, pk=pk)
    require_patient_owner(request.user, cert.patient)
    if not cert.pdf_file:
        messages.error(request, 'PDF not available.')
        return redirect('certificates:detail', pk=pk)
    return FileResponse(cert.pdf_file.open('rb'), as_attachment=True, filename=f'{cert.certificate_number}.pdf')


@doctor_required
def verify(request, pk):
    """Doctors and admins may mark a certificate as verified."""
    cert = get_object_or_404(MedicalCertificate, pk=pk)
    if request.method == 'POST':
        cert.status = MedicalCertificate.STATUS_VERIFIED
        cert.save(update_fields=['status', 'updated_at'])
        log_action(request.user, 'verify', 'certificates', cert.pk, cert.certificate_number, request=request)
        messages.success(request, f'Certificate {cert.certificate_number} verified.')
    return redirect('certificates:detail', pk=pk)
