from django.urls import path
from . import views

app_name = 'consultations'
urlpatterns = [
    path('from-appointment/<int:appointment_id>/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/edit/', views.edit, name='edit'),
]
