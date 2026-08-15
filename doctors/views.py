from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied

from accounts.authorization import is_doctor, is_admin, get_doctor_profile
from .models import Doctor, DoctorSchedule


@login_required
def index(request):
    """
    Admin: all doctors.
    Doctor: only own profile (redirect to detail).
    Patient: directory of active doctors.
    """
    user = request.user
    profile = get_doctor_profile(user)
    if profile is not None and not is_admin(user):
        return redirect('doctors:detail', doctor_id=profile.doctor_id)

    q = request.GET.get('q', '').strip()
    spec = request.GET.get('specialization', '')
    qs = Doctor.objects.filter(status='Active').select_related(
        'specialization', 'department', 'medical_system'
    )
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(doctor_id__icontains=q))
    if spec:
        qs = qs.filter(specialization__code=spec)
    from masters.models import Specialization
    page = Paginator(qs.order_by('name'), 10).get_page(request.GET.get('page'))
    return render(request, 'doctors/list.html', {
        'page_obj': page,
        'doctors': page,
        'q': q, 'spec': spec,
        'specializations': Specialization.objects.filter(status='Active'),
    })


@login_required
def detail(request, doctor_id):
    doctor = get_object_or_404(
        Doctor.objects.select_related('specialization', 'department', 'medical_system'),
        doctor_id=doctor_id,
    )
    profile = get_doctor_profile(request.user)
    if profile is not None and not is_admin(request.user):
        if profile.doctor_id != doctor_id:
            raise PermissionDenied('You can only view your own doctor profile.')
    schedules = DoctorSchedule.objects.filter(doctor=doctor, is_active=True).order_by(
        'day_of_week', 'start_time'
    )
    return render(request, 'doctors/detail.html', {'doctor': doctor, 'schedules': schedules})
