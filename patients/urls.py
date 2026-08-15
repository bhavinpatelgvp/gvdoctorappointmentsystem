from django.urls import path
from . import views

app_name = 'patients'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.doctor_add_patient, name='doctor_add'),
    path('<str:patient_id>/', views.detail, name='detail'),
    path('<str:patient_id>/history/', views.history, name='history'),
    path('<str:patient_id>/edit/', views.doctor_edit_patient, name='doctor_edit'),
    path('<str:patient_id>/toggle/', views.doctor_deactivate_patient, name='doctor_toggle'),
]
