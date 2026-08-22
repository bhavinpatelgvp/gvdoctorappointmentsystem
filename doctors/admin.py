from django.contrib import admin
from django.utils.html import format_html
from .models import Doctor, DoctorSchedule, DoctorLeave


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1
    fields = (
        'day_of_week', 'start_time', 'end_time', 'slot_duration_minutes',
        'max_patients_per_day', 'break_start', 'break_end', 'is_active',
    )
    ordering = ('day_of_week', 'start_time')


class DoctorLeaveInline(admin.TabularInline):
    model = DoctorLeave
    extra = 0
    fields = ('start_date', 'end_date', 'reason')
    ordering = ('-start_date',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'doctor_id', 'name', 'specialization',
        'experience_years', 'availability_badge', 'status_badge', 'mobile',
    )
    list_filter = ('specialization', 'status', 'availability', 'gender')
    search_fields = ('name', 'doctor_id', 'registration_number', 'email', 'mobile')
    list_select_related = ('specialization', 'user')
    autocomplete_fields = ('user', 'specialization', 'department')
    list_per_page = 25
    inlines = [DoctorScheduleInline, DoctorLeaveInline]
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_available', 'mark_unavailable', 'deactivate_doctors']

    fieldsets = (
        ('Identity', {
            'fields': ('doctor_id', 'user', 'name', 'gender', 'profile_photo'),
        }),
        ('Professional', {
            'fields': (
                'qualification', 'specialization',
                'registration_number', 'experience_years',
            ),
        }),
        ('Contact', {
            'fields': ('email', 'mobile'),
        }),
        ('Availability & Status', {
            'fields': ('availability', 'status'),
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Availability')
    def availability_badge(self, obj):
        colors = {
            'Available': '#4a7c59',
            'Unavailable': '#a65d57',
            'On Leave': '#c4a35a',
        }
        color = colors.get(obj.availability, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.availability,
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        color = '#4a7c59' if obj.status == 'Active' else '#a65d57'
        return format_html('<span style="color:{};font-weight:600;">● {}</span>', color, obj.status)

    @admin.action(description='Mark selected as Available')
    def mark_available(self, request, queryset):
        n = queryset.update(availability='Available')
        self.message_user(request, f'{n} doctor(s) marked Available.')

    @admin.action(description='Mark selected as Unavailable')
    def mark_unavailable(self, request, queryset):
        n = queryset.update(availability='Unavailable')
        self.message_user(request, f'{n} doctor(s) marked Unavailable.')

    @admin.action(description='Deactivate selected doctors')
    def deactivate_doctors(self, request, queryset):
        n = queryset.update(status='Inactive')
        self.message_user(request, f'{n} doctor(s) deactivated.')


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'doctor', 'get_day', 'start_time', 'end_time',
        'slot_duration_minutes', 'max_patients_per_day', 'is_active',
    )
    list_filter = ('day_of_week', 'is_active', 'doctor')
    search_fields = ('doctor__name', 'doctor__doctor_id')
    list_select_related = ('doctor',)
    autocomplete_fields = ('doctor',)

    @admin.display(description='Day', ordering='day_of_week')
    def get_day(self, obj):
        return obj.get_day_of_week_display()


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_date', 'end_date', 'duration_days', 'reason', 'created_at')
    list_filter = ('start_date', 'doctor')
    search_fields = ('doctor__name', 'reason')
    date_hierarchy = 'start_date'
    autocomplete_fields = ('doctor',)
    list_select_related = ('doctor',)

    @admin.display(description='Days')
    def duration_days(self, obj):
        if obj.start_date and obj.end_date:
            return (obj.end_date - obj.start_date).days + 1
        return '—'
