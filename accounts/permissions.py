from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from accounts.models import Role


def role_required(*role_codes):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            role = getattr(user, 'role', None)
            if role and role.code in role_codes:
                return view_func(request, *args, **kwargs)
            # Doctor fallback: linked doctor profile counts as doctor access
            if Role.DOCTOR in role_codes:
                try:
                    if user.doctor_profile is not None:
                        return view_func(request, *args, **kwargs)
                except Exception:
                    pass
            raise PermissionDenied("You do not have permission to access this resource.")
        return _wrapped
    return decorator


def admin_required(view_func):
    return role_required(Role.ADMIN, Role.SUPER_ADMIN)(view_func)


def doctor_required(view_func):
    """Doctors, admins, superusers (and users with a doctor_profile)."""
    return role_required(Role.DOCTOR, Role.ADMIN, Role.SUPER_ADMIN)(view_func)
