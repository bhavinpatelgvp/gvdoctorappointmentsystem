from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:doctor_id>/', views.detail, name='detail'),
]
