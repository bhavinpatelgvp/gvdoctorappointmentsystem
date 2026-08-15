"""django-allauth adapters for Google (Gmail) sign-in."""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from accounts.models import Role


class GVAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return reverse('accounts:dashboard')


class GVSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    - Existing user with same email: link and sign in
    - New Gmail user: create account; if no role yet, send to complete-profile
    """

    def pre_social_login(self, request, sociallogin):
        """Connect social account to existing user with the same email."""
        if sociallogin.is_existing:
            return
        email = (sociallogin.account.extra_data.get('email') or '').strip().lower()
        if not email:
            return
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email__iexact=email).order_by('id').first()
            if user:
                sociallogin.connect(request, user)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Username from email local-part if empty
        if not user.username:
            email = (data.get('email') or sociallogin.account.extra_data.get('email') or '').strip()
            base = email.split('@')[0] if email else 'user'
            from django.contrib.auth import get_user_model
            User = get_user_model()
            candidate = base
            n = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f'{base}{n}'
                n += 1
            user.username = candidate
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        # New social users start without a clinical role; complete-profile assigns one
        if not user.role_id:
            user.is_active_user = True
            user.save(update_fields=['is_active_user'])
        return user
