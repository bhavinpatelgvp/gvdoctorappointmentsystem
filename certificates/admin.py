from django.contrib import admin
from django.utils.html import format_html
from .models import MedicalCertificate


@admin.register(MedicalCertificate)
class MedicalCertificateAdmin(admin.ModelAdmin):
    list_display = (
        'certificate_number', 'patient', 'doctor', 'status_badge',
        'consultation_date', 'rest_flag', 'rest_days', 'issued_at',
    )
    list_filter = ('status', 'rest_recommended', 'consultation_date')
    search_fields = (
        'certificate_number', 'patient__name', 'patient__patient_id',
        'doctor__name', 'medical_advice',
    )
    date_hierarchy = 'consultation_date'
    list_select_related = ('patient', 'doctor', 'consultation', 'created_by')
    autocomplete_fields = ('patient', 'doctor', 'consultation', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_issued', 'mark_sent', 'mark_verified', 'mark_cancelled']
    list_per_page = 30

    fieldsets = (
        ('Certificate', {
            'fields': ('certificate_number', 'status', 'pdf_file'),
        }),
        ('Patient & Doctor', {
            'fields': ('patient', 'doctor', 'consultation', 'consultation_date'),
        }),
        ('Medical content', {
            'fields': ('medical_advice', 'remarks'),
        }),
        ('Rest recommendation', {
            'fields': ('rest_recommended', 'rest_start_date', 'rest_end_date', 'rest_days'),
        }),
        ('Issuance', {
            'fields': ('issued_at', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': '#888',
            'issued': '#4a7c59',
            'sent': '#4a6fa5',
            'verified': '#3d5a40',
            'cancelled': '#a65d57',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description='Rest', boolean=True)
    def rest_flag(self, obj):
        return obj.rest_recommended

    @admin.action(description='Mark as Issued')
    def mark_issued(self, request, queryset):
        from django.utils import timezone
        n = queryset.update(status=MedicalCertificate.STATUS_ISSUED, issued_at=timezone.now())
        self.message_user(request, f'{n} certificate(s) marked Issued.')

    @admin.action(description='Mark as Sent')
    def mark_sent(self, request, queryset):
        n = queryset.update(status=MedicalCertificate.STATUS_SENT)
        self.message_user(request, f'{n} certificate(s) marked Sent.')

    @admin.action(description='Mark as Verified')
    def mark_verified(self, request, queryset):
        n = queryset.update(status=MedicalCertificate.STATUS_VERIFIED)
        self.message_user(request, f'{n} certificate(s) marked Verified.')

    @admin.action(description='Mark as Cancelled')
    def mark_cancelled(self, request, queryset):
        n = queryset.update(status=MedicalCertificate.STATUS_CANCELLED)
        self.message_user(request, f'{n} certificate(s) cancelled.')
