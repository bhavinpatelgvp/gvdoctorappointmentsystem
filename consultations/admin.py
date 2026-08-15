from django.contrib import admin
from django.utils.html import format_html
from .models import Consultation


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        'patient', 'doctor', 'consultation_date',
        'rest_flag', 'referral_flag', 'follow_up_date',
    )
    list_filter = ('rest_recommended', 'referral_required', 'consultation_date', 'doctor')
    search_fields = (
        'patient__name', 'patient__patient_id', 'doctor__name',
        'chief_complaint', 'final_diagnosis',
    )
    date_hierarchy = 'consultation_date'
    list_select_related = ('patient', 'doctor', 'appointment', 'created_by')
    autocomplete_fields = ('appointment', 'patient', 'doctor', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 30

    fieldsets = (
        ('Links', {
            'fields': ('appointment', 'patient', 'doctor', 'consultation_date'),
        }),
        ('Clinical assessment', {
            'fields': (
                'chief_complaint', 'symptoms', 'clinical_observations',
                'preliminary_diagnosis', 'final_diagnosis',
            ),
        }),
        ('Treatment', {
            'fields': ('treatment', 'prescription', 'advice', 'additional_notes'),
        }),
        ('Follow-up & rest', {
            'fields': (
                'follow_up_date', 'rest_recommended', 'rest_days',
                'referral_required', 'referral_notes',
            ),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Rest', boolean=True)
    def rest_flag(self, obj):
        return obj.rest_recommended

    @admin.display(description='Referral', boolean=True)
    def referral_flag(self, obj):
        return obj.referral_required
