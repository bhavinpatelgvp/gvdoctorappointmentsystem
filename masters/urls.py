from django.urls import path
from . import views

app_name = 'masters'

urlpatterns = [
    path('', views.master_index, name='index'),

    # Department
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/toggle/', views.department_deactivate, name='department_toggle'),

    # Programme
    path('programmes/', views.programme_list, name='programme_list'),
    path('programmes/add/', views.programme_create, name='programme_create'),
    path('programmes/<int:pk>/edit/', views.programme_edit, name='programme_edit'),
    path('programmes/<int:pk>/toggle/', views.programme_deactivate, name='programme_toggle'),

    # Specialization
    path('specializations/', views.specialization_list, name='specialization_list'),
    path('specializations/add/', views.specialization_create, name='specialization_create'),
    path('specializations/<int:pk>/edit/', views.specialization_edit, name='specialization_edit'),
    path('specializations/<int:pk>/delete/', views.specialization_delete, name='specialization_delete'),

    # HOD
    path('hods/', views.hod_list, name='hod_list'),
    path('hods/add/', views.hod_create, name='hod_create'),
    path('hods/<int:pk>/edit/', views.hod_edit, name='hod_edit'),
    path('hods/<int:pk>/toggle/', views.hod_deactivate, name='hod_toggle'),

    # Doctor master
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/add/', views.doctor_create, name='doctor_create'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('doctors/<int:pk>/edit/', views.doctor_edit, name='doctor_edit'),
    path('doctors/<int:pk>/toggle/', views.doctor_deactivate, name='doctor_toggle'),

    # Student master
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/export/', views.student_export, name='student_export'),
    path('students/import/', views.student_import, name='student_import'),
    path('students/import/template/', views.student_import_template, name='student_import_template'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/toggle/', views.student_deactivate, name='student_toggle'),

    # Staff master
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/toggle/', views.staff_deactivate, name='staff_toggle'),

    # Staff family master
    path('family/', views.family_list, name='family_list'),
    path('family/add/', views.family_create, name='family_create'),
    path('family/<int:pk>/edit/', views.family_edit, name='family_edit'),
    path('family/<int:pk>/toggle/', views.family_deactivate, name='family_toggle'),
]
