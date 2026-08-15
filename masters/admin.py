from django.contrib import admin
from django.utils.html import format_html
from .models import Department, Programme, Specialization, HOD, MedicalSystem


class StatusBadgeMixin:
    @admin.display(description='Status')
    def status_badge(self, obj):
        color = '#4a7c59' if obj.status == 'Active' else '#a65d57'
        return format_html(
            '<span style="color:{};font-weight:600;">● {}</span>', color, obj.status
        )


@admin.register(Department)
class DepartmentAdmin(StatusBadgeMixin, admin.ModelAdmin):
    list_display = ('department_code', 'name', 'email', 'status_badge', 'programme_count', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'department_code', 'email')
    ordering = ('name',)
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('department_code', 'name', 'email', 'status')}),
        ('Timestamps', {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Programmes')
    def programme_count(self, obj):
        return obj.programmes.count()


@admin.register(Programme)
class ProgrammeAdmin(StatusBadgeMixin, admin.ModelAdmin):
    list_display = ('programme_code', 'name', 'department', 'duration_years', 'status_badge')
    list_filter = ('department', 'status', 'duration_years')
    search_fields = ('name', 'programme_code')
    autocomplete_fields = ('department',)
    list_select_related = ('department',)


@admin.register(Specialization)
class SpecializationAdmin(StatusBadgeMixin, admin.ModelAdmin):
    list_display = ('code', 'name', 'status_badge', 'doctor_count')
    list_filter = ('status',)
    search_fields = ('code', 'name')

    @admin.display(description='Doctors')
    def doctor_count(self, obj):
        return obj.doctors.count()


@admin.register(HOD)
class HODAdmin(StatusBadgeMixin, admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'department', 'email', 'mobile', 'status_badge')
    list_filter = ('status', 'department')
    search_fields = ('employee_id', 'name', 'email', 'mobile')
    autocomplete_fields = ('user', 'department')
    list_select_related = ('department', 'user')
    readonly_fields = ('created_at',)


@admin.register(MedicalSystem)
class MedicalSystemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status')
    list_filter = ('status',)
    search_fields = ('code', 'name')
