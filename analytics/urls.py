from django.urls import path
from . import views

app_name = 'analytics'
urlpatterns = [
    path('', views.index, name='index'),
    path('downloads/', views.downloads_hub, name='downloads'),
    path('export/patients/', views.export_patients, name='export_patients'),
    path('export/doctors/', views.export_doctors, name='export_doctors'),
    path('export/appointments/', views.export_appointments, name='export_appointments'),
    path('export/health-checkups/', views.export_health_checkups, name='export_health_checkups'),
    path('export/patient-history/', views.export_patient_history, name='export_patient_history'),
]
