from django.urls import path
from . import views

app_name = 'health_records'
urlpatterns = [
    path('', views.index, name='index'),
    path('entry/', views.entry_start, name='entry_start'),
    path('entry/<str:patient_id>/', views.entry, name='entry'),
    path('bulk/', views.bulk_import, name='bulk_import'),
    path('bulk/template/', views.bulk_template, name='bulk_template'),
    path('<int:pk>/', views.detail, name='detail'),
]
