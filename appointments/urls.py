from django.urls import path
from . import views

app_name = 'appointments'
urlpatterns = [
    path('', views.index, name='index'),
    path('find/', views.find_doctor, name='find_doctor'),
    path('book/', views.book, name='book'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/cancel/', views.cancel, name='cancel'),
    path('<int:pk>/reschedule/', views.reschedule, name='reschedule'),
    path('<int:pk>/confirm/', views.confirm, name='confirm'),
    path('<int:pk>/start/', views.start_consultation, name='start_consultation'),
]
