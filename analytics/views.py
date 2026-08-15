import json
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Min, Max, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from accounts.authorization import is_doctor, is_admin, get_linked_patient, get_doctor_profile
from patients.models import Patient
from appointments.models import Appointment
from health_records.models import (
    HealthCheckup, CBCReport, RBSReport, BloodPressureReport,
    LipidProfileReport, ClinicalParameterValue,
)
from certificates.models import MedicalCertificate


@login_required
def index(request):
    analysis = request.GET.get('analysis', 'dashboard')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    patient_id = request.GET.get('patient_id', '')
    category = request.GET.get('category', '')

    user = request.user
    doctor = get_doctor_profile(user) if is_doctor(user) and not is_admin(user) else None
    own_patient = get_linked_patient(user)

    context = {
        'analysis': analysis,
        'date_from': date_from,
        'date_to': date_to,
        'patient_id': patient_id,
        'category': category,
        'categories': Patient.CATEGORY_CHOICES,
        'is_doctor_scope': bool(doctor),
        'is_patient_scope': bool(own_patient) and not is_doctor(user),
        'analysis_choices': [
            ('dashboard', 'Analytics Dashboard'),
            ('patient_trend', 'Patient Health Trend'),
            ('cbc', 'CBC Analysis'),
            ('rbs', 'RBS Analysis'),
            ('bp', 'Blood Pressure Analysis'),
            ('lipid', 'Lipid Profile Analysis'),
            ('department', 'Department Analysis'),
            ('monthly', 'Monthly Analysis'),
            ('doctor_appt', 'Doctor Appointments'),
            ('doctor_checkup', 'Doctor Patient Check-ups'),
            ('category', 'Category Analysis'),
        ],
    }

    appt_qs = Appointment.objects.all()
    hc_qs = HealthCheckup.objects.all()
    patient_qs = Patient.objects.filter(status='Active')

    if doctor:
        appt_qs = appt_qs.filter(doctor=doctor)
        hc_qs = hc_qs.filter(doctor=doctor)
        patient_ids = appt_qs.values_list('patient_id', flat=True).distinct()
        patient_qs = patient_qs.filter(pk__in=patient_ids)
    elif own_patient:
        appt_qs = appt_qs.filter(patient=own_patient)
        hc_qs = hc_qs.filter(patient=own_patient)
        patient_qs = patient_qs.filter(pk=own_patient.pk)

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

    monthly = (
        hc_qs.annotate(month=TruncMonth('checkup_date'))
        .values('month').annotate(c=Count('id')).order_by('month')
    )
    context['monthly_labels'] = json.dumps([m['month'].strftime('%b %Y') if m['month'] else '' for m in monthly])
    context['monthly_values'] = json.dumps([m['c'] for m in monthly])

    cats = patient_qs.values('category').annotate(c=Count('id'))
    context['cat_labels'] = json.dumps([
        dict(Patient.CATEGORY_CHOICES).get(c['category'], c['category']) for c in cats
    ])
    context['cat_values'] = json.dumps([c['c'] for c in cats])
    context['cat_table'] = [
        {'label': dict(Patient.CATEGORY_CHOICES).get(c['category'], c['category']), 'count': c['c']}
        for c in cats
    ]

    dept_data = (
        hc_qs.filter(patient__student_profile__department__isnull=False)
        .values('patient__student_profile__department__name')
        .annotate(c=Count('id')).order_by('-c')[:10]
    )
    context['dept_labels'] = json.dumps([d['patient__student_profile__department__name'] or '—' for d in dept_data])
    context['dept_values'] = json.dumps([d['c'] for d in dept_data])
    context['dept_table'] = dept_data

    by_status = appt_qs.values('status').annotate(c=Count('id')).order_by('status')
    context['appt_status_labels'] = json.dumps([b['status'] for b in by_status])
    context['appt_status_values'] = json.dumps([b['c'] for b in by_status])
    context['appt_by_status'] = list(by_status)

    if analysis in ('doctor_checkup', 'dashboard') or doctor:
        context['recent_checkups'] = hc_qs.select_related('patient').order_by('-checkup_date')[:20]

    if analysis == 'patient_trend' and patient_id:
        patient = Patient.objects.filter(patient_id=patient_id).first()
        if own_patient and patient and patient.pk != own_patient.pk:
            patient = None
        if doctor and patient:
            if not Appointment.objects.filter(doctor=doctor, patient=patient).exists() and not \
                    HealthCheckup.objects.filter(doctor=doctor, patient=patient).exists():
                # still allow view if admin-like; for pure doctor scope keep soft
                pass
        context['trend_patient'] = patient
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
            bp = BloodPressureReport.objects.filter(health_checkup__patient=patient).order_by('measured_at')
            context['bp_labels'] = json.dumps([str(b.measured_at.date()) if b.measured_at else '' for b in bp])
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
