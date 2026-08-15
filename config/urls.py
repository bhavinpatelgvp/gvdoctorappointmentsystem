from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('accounts:dashboard') if r.user.is_authenticated else redirect('accounts:login')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),  # Google / social login
    path('masters/', include('masters.urls')),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('appointments/', include('appointments.urls')),
    path('consultations/', include('consultations.urls')),
    path('health/', include('health_records.urls')),
    path('certificates/', include('certificates.urls')),
    path('analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
