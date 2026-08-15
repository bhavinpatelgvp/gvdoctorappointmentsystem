import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Min, Max
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect

from accounts.authorization import is_doctor, is_admin, get_linked_patient, get_doctor_profile
from patients.models import Patient
from appointments.models import Appointment
from health_records.models import (
    HealthCheckup, CBCReport, RBSReport, BloodPressureReport,
    LipidProfileReport, ClinicalParameterValue,
)
from certificates.models import MedicalCertificate


def _qs_params(request, extra=None):
    """Preserve current filters in pagination links."""
    params = request.GET.copy()
    params.pop('page', None)
    if extra:
        for k, v in extra.items():
            if v is None or v == '':
                params.pop(k, None)
            else:
                params[k] = v
    return params.urlencode()


@login_required
def index(request):
    analysis = request.GET.get('analysis', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    patient_id = request.GET.get('patient_id', '')
    category = request.GET.get('category', '')

    user = request.user
    doctor = get_doctor_profile(user) if is_doctor(user) and not is_admin(user) else None
    own_patient = get_linked_patient(user)
    is_patient_scope = bool(own_patient) and not is_doctor(user) and not is_admin(user)
    is_doctor_scope = bool(doctor)

    # Patient workspace: lock to own category only (never show all categories)
    if is_patient_scope:
        category = own_patient.category
        patient_id = own_patient.patient_id
        # Patients only need a focused set of analysis types
        analysis_choices = [
            ('', '— Select analysis type —'),
            ('monthly', 'Monthly Check-ups'),
            ('patient_trend', 'My Health Trend'),
            ('cbc', 'CBC Analysis'),
            ('rbs', 'RBS Analysis'),
            ('bp', 'Blood Pressure Analysis'),
            ('lipid', 'Lipid Profile Analysis'),
        ]
        if analysis and analysis not in dict(analysis_choices):
            analysis = ''
    else:
        analysis_choices = [
            ('', '— Select analysis type —'),
            ('patient_categories', 'Patient Categories'),
            ('monthly', 'Monthly Check-ups'),
            ('department', 'Department-wise Check-ups'),
            ('category', 'Category breakdown'),
            ('doctor_appt', 'Appointments by Status (Yours)'),
            ('doctor_checkup', 'Recent Check-ups (Yours)'),
            ('patient_trend', 'Patient Health Trend'),
            ('cbc', 'CBC Analysis'),
            ('rbs', 'RBS Analysis'),
            ('bp', 'Blood Pressure Analysis'),
            ('lipid', 'Lipid Profile Analysis'),
        ]
        if analysis and analysis not in dict(analysis_choices):
            analysis = '' 

    context = {
        'analysis': analysis,
        'date_from': date_from,
        'date_to': date_to,
        'patient_id': patient_id,
        'category': category,
        'categories': Patient.CATEGORY_CHOICES,
        'is_doctor_scope': is_doctor_scope,
        'is_patient_scope': is_patient_scope,
        'analysis_choices': analysis_choices,
        'category_locked': is_patient_scope,
        'querystring': _qs_params(request),
    }

    appt_qs = Appointment.objects.all()
    hc_qs = HealthCheckup.objects.all()
    patient_qs = Patient.objects.filter(status='Active')

    if doctor:
        appt_qs = appt_qs.filter(doctor=doctor)
        hc_qs = hc_qs.filter(doctor=doctor)
        patient_ids = set(appt_qs.values_list('patient_id', flat=True)) | set(
            hc_qs.values_list('patient_id', flat=True)
        )
        patient_qs = patient_qs.filter(pk__in=patient_ids)
    elif is_patient_scope:
        appt_qs = appt_qs.filter(patient=own_patient)
        hc_qs = hc_qs.filter(patient=own_patient)
        patient_qs = patient_qs.filter(pk=own_patient.pk)

    # Category filter applies to all roles (for patients it is forced above)
    if category:
        patient_qs = patient_qs.filter(category=category)
        appt_qs = appt_qs.filter(patient__category=category)
        hc_qs = hc_qs.filter(patient__category=category)

    if date_from:
        appt_qs = appt_qs.filter(appointment_date__gte=date_from)
        hc_qs = hc_qs.filter(checkup_date__gte=date_from)
    if date_to:
        appt_qs = appt_qs.filter(appointment_date__lte=date_to)
        hc_qs = hc_qs.filter(checkup_date__lte=date_to)

    context['kpi'] = {
        'patients': patient_qs.count(),
        'checkups': hc_qs.count(),
        'cbc': CBCReport.objects.filter(health_checkup__in=hc_qs).count(),
        'rbs': RBSReport.objects.filter(health_checkup__in=hc_qs).count(),
        'bp': BloodPressureReport.objects.filter(health_checkup__in=hc_qs).count(),
        'lipid': LipidProfileReport.objects.filter(health_checkup__in=hc_qs).count(),
        'appointments': appt_qs.count(),
        'certificates': MedicalCertificate.objects.filter(patient__in=patient_qs).count(),
    }

    # ---- Charts / tables driven by filters (analysis type) — nothing shown until a type is chosen ----
    show_monthly = analysis == 'monthly'
    show_categories = analysis in ('category', 'patient_categories') and not is_patient_scope
    show_department = analysis == 'department' and not is_patient_scope
    show_appt_status = analysis == 'doctor_appt'
    show_recent_checkups = analysis == 'doctor_checkup'
    show_kpi = analysis in (
        'monthly', 'category', 'patient_categories', 'department',
        'doctor_appt', 'doctor_checkup',
    )

    context['show_monthly'] = show_monthly
    context['show_categories'] = show_categories
    context['show_department'] = show_department
    context['show_appt_status'] = show_appt_status
    context['show_recent_checkups'] = show_recent_checkups
    context['show_kpi'] = show_kpi

    # Defaults so template JS never breaks
    context['monthly_labels'] = '[]'
    context['monthly_values'] = '[]'
    context['cat_labels'] = '[]'
    context['cat_values'] = '[]'
    context['cat_table'] = []
    context['dept_labels'] = '[]'
    context['dept_values'] = '[]'
    context['dept_table'] = []
    context['appt_status_labels'] = '[]'
    context['appt_status_values'] = '[]'
    context['appt_by_status'] = []
    context['recent_checkups'] = []
    context['page_obj'] = None

    if show_monthly:
        monthly = (
            hc_qs.annotate(month=TruncMonth('checkup_date'))
            .values('month').annotate(c=Count('id')).order_by('month')
        )
        context['monthly_labels'] = json.dumps([
            m['month'].strftime('%b %Y') if m['month'] else '' for m in monthly
        ])
        context['monthly_values'] = json.dumps([m['c'] for m in monthly])

    if show_categories:
        cats = patient_qs.values('category').annotate(c=Count('id'))
        context['cat_labels'] = json.dumps([
            dict(Patient.CATEGORY_CHOICES).get(c['category'], c['category']) for c in cats
        ])
        context['cat_values'] = json.dumps([c['c'] for c in cats])
        context['cat_table'] = [
            {
                'label': dict(Patient.CATEGORY_CHOICES).get(c['category'], c['category']),
                'count': c['c'],
            }
            for c in cats
        ]

    if show_department:
        dept_data = list(
            hc_qs.filter(patient__student_profile__department__isnull=False)
            .values('patient__student_profile__department__name')
            .annotate(c=Count('id')).order_by('-c')[:10]
        )
        context['dept_labels'] = json.dumps([
            d['patient__student_profile__department__name'] or '—' for d in dept_data
        ])
        context['dept_values'] = json.dumps([d['c'] for d in dept_data])
        context['dept_table'] = dept_data

    if show_appt_status:
        by_status = list(appt_qs.values('status').annotate(c=Count('id')).order_by('status'))
        context['appt_status_labels'] = json.dumps([b['status'] for b in by_status])
        context['appt_status_values'] = json.dumps([b['c'] for b in by_status])
        context['appt_by_status'] = by_status

    if show_recent_checkups:
        recent_qs = hc_qs.select_related('patient').order_by('-checkup_date')
        paginator = Paginator(recent_qs, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        context['page_obj'] = page_obj
        context['recent_checkups'] = page_obj

    # Patient health trend
    if analysis == 'patient_trend':
        patient = None
        if is_patient_scope:
            patient = own_patient
        elif patient_id:
            patient = Patient.objects.filter(patient_id=patient_id).first()
            if doctor and patient:
                # Soft scope: prefer patients linked via appts/checkups; still allow if found
                pass
        context['trend_patient'] = patient
        context['hb_labels'] = '[]'
        context['hb_values'] = '[]'
        context['rbs_labels'] = '[]'
        context['rbs_values'] = '[]'
        context['bp_labels'] = '[]'
        context['bp_sys'] = '[]'
        context['bp_dia'] = '[]'
        if patient:
            hb = ClinicalParameterValue.objects.filter(
                health_checkup__patient=patient, parameter__code='HB'
            ).select_related('health_checkup').order_by('health_checkup__checkup_date')
            rbs = ClinicalParameterValue.objects.filter(
                health_checkup__patient=patient, parameter__code='RBS'
            ).select_related('health_checkup').order_by('health_checkup__checkup_date')
            context['hb_labels'] = json.dumps([str(v.health_checkup.checkup_date) for v in hb])
            context['hb_values'] = json.dumps([float(v.value) for v in hb])
            context['rbs_labels'] = json.dumps([str(v.health_checkup.checkup_date) for v in rbs])
            context['rbs_values'] = json.dumps([float(v.value) for v in rbs])
            bp = BloodPressureReport.objects.filter(
                health_checkup__patient=patient
            ).order_by('measured_at')
            context['bp_labels'] = json.dumps([
                str(b.measured_at.date()) if b.measured_at else '' for b in bp
            ])
            context['bp_sys'] = json.dumps([b.systolic for b in bp])
            context['bp_dia'] = json.dumps([b.diastolic for b in bp])

    if analysis == 'cbc':
        cbc_qs = CBCReport.objects.filter(health_checkup__in=hc_qs)
        context['cbc_stats'] = cbc_qs.aggregate(
            avg=Avg('hemoglobin'), mn=Min('hemoglobin'), mx=Max('hemoglobin'), n=Count('id')
        )
    if analysis == 'rbs':
        rbs_qs = RBSReport.objects.filter(health_checkup__in=hc_qs)
        context['rbs_stats'] = rbs_qs.aggregate(
            avg=Avg('value'), mn=Min('value'), mx=Max('value'), n=Count('id')
        )
    if analysis == 'bp':
        bp_qs = BloodPressureReport.objects.filter(health_checkup__in=hc_qs)
        context['bp_stats'] = bp_qs.aggregate(
            avg_sys=Avg('systolic'), avg_dia=Avg('diastolic'), n=Count('id')
        )
    if analysis == 'lipid':
        lip_qs = LipidProfileReport.objects.filter(health_checkup__in=hc_qs)
        context['lipid_stats'] = lip_qs.aggregate(
            avg_tc=Avg('total_cholesterol'), avg_hdl=Avg('hdl'), avg_ldl=Avg('ldl'), n=Count('id')
        )

    return render(request, 'analytics/dashboard.html', context)


# ── Exports (CSV downloads with filters) ─────────────────────
import csv
from django.http import HttpResponse
from django.contrib import messages
from accounts.permissions import admin_required
from accounts.authorization import is_doctor, is_admin, get_doctor_profile, get_linked_patient
from doctors.models import Doctor
from datetime import datetime


def _apply_export_filters(request, qs, date_field='created_at', patient_field='patient'):
    """Common filters: patient_id, category, from, to, year."""
    patient_id = request.GET.get('patient_id', '').strip()
    category = request.GET.get('category', '').strip()
    date_from = request.GET.get('from', '').strip()
    date_to = request.GET.get('to', '').strip()
    year = request.GET.get('year', '').strip()
    if patient_id:
        qs = qs.filter(**{f'{patient_field}__patient_id': patient_id})
    if category:
        qs = qs.filter(**{f'{patient_field}__category': category})
    if date_from:
        qs = qs.filter(**{f'{date_field}__gte': date_from})
    if date_to:
        qs = qs.filter(**{f'{date_field}__lte': date_to})
    if year:
        try:
            y = int(year)
            qs = qs.filter(**{f'{date_field}__year': y})
        except ValueError:
            pass
    return qs


@login_required
def export_patients(request):
    """Admin/Doctor: export patients (scoped for doctor)."""
    user = request.user
    if not (is_admin(user) or is_doctor(user)):
        messages.error(request, 'Permission denied.')
        return redirect('analytics:index')
    qs = Patient.objects.filter(status='Active').select_related(
        'student_profile', 'staff_profile', 'family_profile'
    ).order_by('name')
    doctor = get_doctor_profile(user) if is_doctor(user) and not is_admin(user) else None
    if doctor:
        # Patients who had appt or checkup with this doctor
        from appointments.models import Appointment
        from health_records.models import HealthCheckup
        pids = set(
            Appointment.objects.filter(doctor=doctor).values_list('patient_id', flat=True)
        ) | set(
            HealthCheckup.objects.filter(doctor=doctor).values_list('patient_id', flat=True)
        )
        qs = qs.filter(pk__in=pids)
    category = request.GET.get('category', '').strip()
    patient_id = request.GET.get('patient_id', '').strip()
    if category:
        qs = qs.filter(category=category)
    if patient_id:
        qs = qs.filter(patient_id=patient_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patients_export.csv"'
    w = csv.writer(response)
    w.writerow(['Patient ID', 'Name', 'Category', 'Mobile', 'Email', 'Gender', 'DOB', 'Status'])
    for p in qs:
        w.writerow([
            p.patient_id, p.name, p.get_category_display(), p.mobile or '',
            p.email or '', getattr(p, 'gender', '') or '', getattr(p, 'date_of_birth', '') or '',
            p.status,
        ])
    return response


@login_required
def export_doctors(request):
    """Admin only: export doctors."""
    if not is_admin(request.user):
        messages.error(request, 'Permission denied.')
        return redirect('analytics:index')
    qs = Doctor.objects.select_related('user', 'specialization').order_by('user__first_name')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="doctors_export.csv"'
    w = csv.writer(response)
    w.writerow(['Doctor ID', 'Name', 'Specialization', 'Mobile', 'Email', 'Status'])
    for d in qs:
        name = d.user.get_full_name() if d.user else str(d)
        w.writerow([
            getattr(d, 'doctor_id', d.pk), name,
            d.specialization.name if d.specialization else '',
            getattr(d, 'mobile', '') or '', getattr(d.user, 'email', '') if d.user else '',
            d.status,
        ])
    return response


@login_required
def export_appointments(request):
    """Admin/Doctor: export appointments with filters."""
    user = request.user
    if not (is_admin(user) or is_doctor(user)):
        messages.error(request, 'Permission denied.')
        return redirect('analytics:index')
    qs = Appointment.objects.select_related('patient', 'doctor', 'doctor__user').order_by('-appointment_date')
    doctor = get_doctor_profile(user) if is_doctor(user) and not is_admin(user) else None
    if doctor:
        qs = qs.filter(doctor=doctor)
    qs = _apply_export_filters(request, qs, date_field='appointment_date', patient_field='patient')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="appointments_export.csv"'
    w = csv.writer(response)
    w.writerow(['Date', 'Time', 'Patient ID', 'Patient', 'Doctor', 'Status', 'Reason'])
    for a in qs:
        doc_name = a.doctor.user.get_full_name() if a.doctor and a.doctor.user else ''
        w.writerow([
            a.appointment_date, a.appointment_time, a.patient.patient_id, a.patient.name,
            doc_name, a.status, getattr(a, 'reason', '') or '',
        ])
    return response


@login_required
def export_health_checkups(request):
    """Admin/Doctor: export health checkups with filters."""
    user = request.user
    if not (is_admin(user) or is_doctor(user)):
        messages.error(request, 'Permission denied.')
        return redirect('analytics:index')
    qs = HealthCheckup.objects.select_related('patient', 'doctor', 'doctor__user').order_by('-checkup_date')
    doctor = get_doctor_profile(user) if is_doctor(user) and not is_admin(user) else None
    if doctor:
        qs = qs.filter(doctor=doctor)
    qs = _apply_export_filters(request, qs, date_field='checkup_date', patient_field='patient')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="health_checkups_export.csv"'
    w = csv.writer(response)
    w.writerow(['Checkup Date', 'Patient ID', 'Patient', 'Doctor', 'Notes', 'Category'])
    for h in qs:
        doc_name = h.doctor.user.get_full_name() if h.doctor and h.doctor.user else ''
        w.writerow([
            h.checkup_date, h.patient.patient_id, h.patient.name, doc_name,
            (h.notes or '')[:200], h.patient.get_category_display(),
        ])
    return response


@login_required
def export_patient_history(request):
    """Patient (or admin/doctor viewing a patient): export own/selected patient history."""
    user = request.user
    own = get_linked_patient(user)
    patient_id = request.GET.get('patient_id', '').strip()
    date_from = request.GET.get('from', '').strip()
    date_to = request.GET.get('to', '').strip()

    if own and not is_admin(user) and not is_doctor(user):
        patient = own
    elif patient_id:
        patient = Patient.objects.filter(patient_id=patient_id).first()
        if not patient:
            messages.error(request, 'Patient not found.')
            return redirect('analytics:index')
        if is_doctor(user) and not is_admin(user):
            from accounts.authorization import doctor_can_access_patient
            if not doctor_can_access_patient(user, patient):
                messages.error(request, 'Access denied.')
                return redirect('analytics:index')
    else:
        messages.error(request, 'Specify patient or login as patient.')
        return redirect('analytics:index')

    hc_qs = HealthCheckup.objects.filter(patient=patient).order_by('-checkup_date')
    if date_from:
        hc_qs = hc_qs.filter(checkup_date__gte=date_from)
    if date_to:
        hc_qs = hc_qs.filter(checkup_date__lte=date_to)

    response = HttpResponse(content_type='text/csv')
    fname = f"patient_{patient.patient_id}_history.csv"
    response['Content-Disposition'] = f'attachment; filename="{fname}"'
    w = csv.writer(response)
    w.writerow(['Type', 'Date', 'Details', 'Notes'])
    for h in hc_qs:
        w.writerow(['Health Checkup', h.checkup_date, '', (h.notes or '')[:300]])
    appts = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
    if date_from:
        appts = appts.filter(appointment_date__gte=date_from)
    if date_to:
        appts = appts.filter(appointment_date__lte=date_to)
    for a in appts:
        w.writerow(['Appointment', a.appointment_date, a.status, getattr(a, 'reason', '') or ''])
    certs = MedicalCertificate.objects.filter(patient=patient).order_by('-created_at')
    for c in certs:
        w.writerow(['Certificate', c.created_at.date() if c.created_at else '', getattr(c, 'certificate_type', '') or '', ''])
    return response


@login_required
def downloads_hub(request):
    """Page with download buttons and filter form for admin/doctor/patient."""
    user = request.user
    is_adm = is_admin(user)
    is_doc = is_doctor(user) and not is_adm
    own = get_linked_patient(user)
    is_pat = bool(own) and not is_adm and not is_doc
    years = list(range(datetime.now().year, datetime.now().year - 6, -1))
    return render(request, 'analytics/downloads.html', {
        'is_admin': is_adm,
        'is_doctor': is_doc,
        'is_patient': is_pat,
        'own_patient': own,
        'categories': Patient.CATEGORY_CHOICES,
        'years': years,
        'date_from': request.GET.get('from', ''),
        'date_to': request.GET.get('to', ''),
        'category': request.GET.get('category', ''),
        'patient_id': request.GET.get('patient_id', ''),
        'year': request.GET.get('year', ''),
    })
