"""
Force authentication for the whole application.
Unauthenticated requests are redirected to the login page.
Public paths: login, register, logout, static, media, Django admin login.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404


class LoginRequiredMiddleware:
    """
    Session-aware gate: no page opens without a valid logged-in session,
    except explicitly public routes.
    """

    # Path prefixes that do not require login
    PUBLIC_PREFIXES = (
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/logout/',
        '/static/',
        '/media/',
        '/admin/login/',  # Django admin has its own auth
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Always allow public prefixes
        if any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            return self.get_response(request)

        # Allow Django admin only if already authenticated (admin uses its own login)
        if path.startswith('/admin/'):
            if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
                return self.get_response(request)
            # Send staff to admin login; others to app login
            if path.startswith('/admin/login'):
                return self.get_response(request)
            return redirect(f"{reverse('admin:login')}?next={path}")

        # Everything else requires an authenticated session
        if not request.user.is_authenticated:
            login_url = reverse(getattr(settings, 'LOGIN_URL', 'accounts:login'))
            # Preserve next so user returns to intended page after login
            if path and path != '/':
                return redirect(f'{login_url}?next={path}')
            return redirect(login_url)

        # Optional: re-check profile still active on each request (soft)
        # If user was deactivated after login, force logout
        user = request.user
        if not user.is_active or not getattr(user, 'is_active_user', True):
            from django.contrib.auth import logout
            logout(request)
            login_url = reverse(getattr(settings, 'LOGIN_URL', 'accounts:login'))
            return redirect(f'{login_url}?session=expired')

        return self.get_response(request)
