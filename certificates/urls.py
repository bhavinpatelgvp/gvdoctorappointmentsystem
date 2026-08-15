from django.urls import path
from . import views

app_name = 'certificates'
urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/download/', views.download, name='download'),
    path('<int:pk>/verify/', views.verify, name='verify'),
]
