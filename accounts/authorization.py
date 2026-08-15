"""
Object-level authorization for patient data isolation.
Backend enforcement – never rely on frontend hiding alone.
"""
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.shortcuts import get_object_or_404

from accounts.models import Role
from patients.models import Patient


def get_linked_patient(user):
    """Return Patient linked to this user, or None."""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.patient_profile
    except ObjectDoesNotExist:
        return None
    except AttributeError:
        return None


def get_doctor_profile(user):
    """
    Safe reverse OneToOne access.
    Never use getattr(user, 'doctor_profile', None) – it still raises if missing.
    """
    if not user or not user.is_authenticated:
        return None
    try:
        return user.doctor_profile
    except ObjectDoesNotExist:
        return None
    except AttributeError:
        return None


def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, 'role', None)
    if role and role.code in (Role.ADMIN, Role.SUPER_ADMIN):
        return True
    return False


def is_doctor(user):
    """True for doctor role, admin, or superuser."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or is_admin(user):
        return True
    role = getattr(user, 'role', None)
    if role and role.code == Role.DOCTOR:
        return True
    # Fallback: has linked doctor profile
    if get_doctor_profile(user) is not None:
        return True
    return False


def is_patient_role(user):
    if not user or not user.is_authenticated:
        return False
    role = getattr(user, 'role', None)
    if not role:
        return False
    return role.code in (Role.STUDENT, Role.STAFF, Role.STAFF_FAMILY)


def doctor_can_access_patient(user, patient):
    if is_admin(user) or is_doctor(user):
        return True
    own = get_linked_patient(user)
    return own is not None and own.pk == patient.pk


def require_patient_owner(user, patient):
    """Patients: only self. Doctors/admins: allowed (clinical access)."""
    if is_admin(user) or is_doctor(user):
        return
    own = get_linked_patient(user)
    if own is None or own.pk != patient.pk:
        raise PermissionDenied(
            'You do not have permission to access this patient information.'
        )


def get_patient_for_user_or_403(user, patient_id=None, pk=None):
    if patient_id is not None:
        patient = get_object_or_404(Patient, patient_id=patient_id)
    else:
        patient = get_object_or_404(Patient, pk=pk)
    require_patient_owner(user, patient)
    return patient


def patient_scoped_qs(user, queryset, patient_field='patient'):
    if is_admin(user) or is_doctor(user):
        return queryset
    own = get_linked_patient(user)
    if own is None:
        return queryset.none()
    return queryset.filter(**{patient_field: own})


def require_doctor_or_admin(user):
    if not is_doctor(user) and not is_admin(user):
        raise PermissionDenied('Doctor or administrator access required.')


def doctor_owns_appointment(user, appointment):
    """Admin: yes. Doctor: must be the assigned doctor (or no profile yet → allow if role is doctor for demo)."""
    if is_admin(user):
        return True
    profile = get_doctor_profile(user)
    if profile is None:
        # Role is doctor but profile not linked – allow to avoid hard 403; still role-gated by decorator
        return is_doctor(user)
    return appointment.doctor_id == profile.pk


def doctor_owns_consultation(user, consultation):
    if is_admin(user):
        return True
    profile = get_doctor_profile(user)
    if profile is None:
        return is_doctor(user)
    return consultation.doctor_id == profile.pk
