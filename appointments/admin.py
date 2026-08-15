from django.contrib import admin
from django.utils.html import format_html
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'appointment_number', 'patient', 'doctor',
        'appointment_date', 'appointment_time', 'status_badge', 'created_at',
    )
    list_filter = ('status', 'appointment_date', 'doctor__specialization')
    search_fields = (
        'appointment_number', 'patient__name', 'patient__patient_id',
        'doctor__name', 'doctor__doctor_id', 'reason',
    )
    date_hierarchy = 'appointment_date'
    list_select_related = ('patient', 'doctor', 'created_by')
    autocomplete_fields = ('patient', 'doctor', 'created_by')
    list_per_page = 40
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled', 'mark_no_show']

    fieldsets = (
        (None, {
            'fields': ('appointment_number', 'patient', 'doctor'),
        }),
        ('Schedule', {
            'fields': ('appointment_date', 'appointment_time', 'status'),
        }),
        ('Details', {
            'fields': ('reason', 'notes', 'cancelled_reason'),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'requested': '#c4a35a',
            'confirmed': '#4a7c59',
            'in_consultation': '#4a6fa5',
            'completed': '#3d5a40',
            'cancelled': '#a65d57',
            'rescheduled': '#8b6914',
            'no_show': '#666',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.action(description='Mark as Confirmed')
    def mark_confirmed(self, request, queryset):
        n = queryset.update(status=Appointment.STATUS_CONFIRMED)
        self.message_user(request, f'{n} appointment(s) confirmed.')

    @admin.action(description='Mark as Completed')
    def mark_completed(self, request, queryset):
        n = queryset.update(status=Appointment.STATUS_COMPLETED)
        self.message_user(request, f'{n} appointment(s) completed.')

    @admin.action(description='Mark as Cancelled')
    def mark_cancelled(self, request, queryset):
        n = queryset.update(status=Appointment.STATUS_CANCELLED)
        self.message_user(request, f'{n} appointment(s) cancelled.')

    @admin.action(description='Mark as No-show')
    def mark_no_show(self, request, queryset):
        n = queryset.update(status=Appointment.STATUS_NO_SHOW)
        self.message_user(request, f'{n} appointment(s) marked no-show.')
