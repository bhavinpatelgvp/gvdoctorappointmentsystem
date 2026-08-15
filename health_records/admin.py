from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClinicalParameter, HealthCheckup, ClinicalParameterValue,
    CBCReport, RBSReport, BloodPressureReport, LipidProfileReport, BulkImportLog,
)


@admin.register(ClinicalParameter)
class ClinicalParameterAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'category', 'unit',
        'range_display', 'gender_specific', 'is_active', 'display_order',
    )
    list_filter = ('category', 'is_active', 'gender_specific')
    search_fields = ('code', 'name')
    list_editable = ('display_order', 'is_active')
    ordering = ('category', 'display_order', 'name')
    list_per_page = 40

    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'category', 'unit', 'display_order', 'is_active'),
        }),
        ('Default reference range', {
            'fields': ('reference_min', 'reference_max'),
        }),
        ('Gender-specific ranges', {
            'classes': ('collapse',),
            'fields': ('gender_specific', 'male_min', 'male_max', 'female_min', 'female_max'),
        }),
    )

    @admin.display(description='Reference range')
    def range_display(self, obj):
        if obj.reference_min is not None or obj.reference_max is not None:
            return f'{obj.reference_min or "—"} – {obj.reference_max or "—"} {obj.unit}'
        return '—'


class ClinicalParameterValueInline(admin.TabularInline):
    model = ClinicalParameterValue
    extra = 0
    autocomplete_fields = ('parameter',)
    readonly_fields = ('recorded_at',)
    fields = ('parameter', 'value', 'unit', 'status', 'remarks', 'recorded_at')


class CBCReportInline(admin.StackedInline):
    model = CBCReport
    extra = 0
    can_delete = False
    classes = ('collapse',)


class RBSReportInline(admin.StackedInline):
    model = RBSReport
    extra = 0
    can_delete = False
    classes = ('collapse',)


class LipidProfileReportInline(admin.StackedInline):
    model = LipidProfileReport
    extra = 0
    can_delete = False
    classes = ('collapse',)


class BloodPressureReportInline(admin.TabularInline):
    model = BloodPressureReport
    extra = 0
    classes = ('collapse',)
    fields = ('systolic', 'diastolic', 'pulse_rate', 'position', 'measured_at', 'remarks')


@admin.register(HealthCheckup)
class HealthCheckupAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'checkup_date', 'doctor', 'demo_flag', 'param_count', 'created_at')
    list_filter = ('checkup_date', 'is_demo', 'doctor')
    search_fields = ('patient__name', 'patient__patient_id', 'notes')
    date_hierarchy = 'checkup_date'
    list_select_related = ('patient', 'doctor', 'entered_by')
    autocomplete_fields = ('patient', 'doctor', 'entered_by')
    readonly_fields = ('created_at',)
    inlines = [
        ClinicalParameterValueInline,
        CBCReportInline,
        RBSReportInline,
        BloodPressureReportInline,
        LipidProfileReportInline,
    ]

    @admin.display(description='Demo', boolean=True)
    def demo_flag(self, obj):
        return obj.is_demo

    @admin.display(description='Params')
    def param_count(self, obj):
        return obj.parameter_values.count()


@admin.register(ClinicalParameterValue)
class ClinicalParameterValueAdmin(admin.ModelAdmin):
    list_display = ('health_checkup', 'parameter', 'value', 'unit', 'status_badge', 'recorded_at')
    list_filter = ('status', 'parameter__category', 'parameter')
    search_fields = ('health_checkup__patient__name', 'parameter__code', 'parameter__name')
    list_select_related = ('health_checkup', 'health_checkup__patient', 'parameter')
    autocomplete_fields = ('health_checkup', 'parameter')
    readonly_fields = ('recorded_at',)

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'normal': '#4a7c59',
            'abnormal': '#a65d57',
            'unknown': '#888',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="color:{};font-weight:600;">● {}</span>',
            color, obj.get_status_display(),
        )


@admin.register(CBCReport)
class CBCReportAdmin(admin.ModelAdmin):
    list_display = (
        'health_checkup', 'hemoglobin', 'rbc_count', 'wbc_count',
        'platelet_count', 'neutrophils', 'lymphocytes', 'created_at',
    )
    search_fields = ('health_checkup__patient__name',)
    list_select_related = ('health_checkup', 'health_checkup__patient')
    autocomplete_fields = ('health_checkup', 'entered_by')
    readonly_fields = ('created_at',)


@admin.register(RBSReport)
class RBSReportAdmin(admin.ModelAdmin):
    list_display = ('health_checkup', 'value', 'unit', 'remarks', 'created_at')
    search_fields = ('health_checkup__patient__name',)
    list_select_related = ('health_checkup', 'health_checkup__patient')
    autocomplete_fields = ('health_checkup', 'entered_by')
    readonly_fields = ('created_at',)


@admin.register(BloodPressureReport)
class BloodPressureReportAdmin(admin.ModelAdmin):
    list_display = (
        'health_checkup', 'bp_display', 'pulse_rate', 'position',
        'measured_at', 'recorded_by',
    )
    list_filter = ('measured_at',)
    search_fields = ('health_checkup__patient__name',)
    date_hierarchy = 'measured_at'
    list_select_related = ('health_checkup', 'health_checkup__patient', 'recorded_by')
    autocomplete_fields = ('health_checkup', 'recorded_by')
    readonly_fields = ('created_at',)

    @admin.display(description='BP (sys/dia)')
    def bp_display(self, obj):
        return format_html('<strong>{}/{}</strong>', obj.systolic, obj.diastolic)


@admin.register(LipidProfileReport)
class LipidProfileReportAdmin(admin.ModelAdmin):
    list_display = (
        'health_checkup', 'total_cholesterol', 'hdl', 'ldl',
        'triglycerides', 'vldl', 'created_at',
    )
    search_fields = ('health_checkup__patient__name',)
    list_select_related = ('health_checkup', 'health_checkup__patient')
    autocomplete_fields = ('health_checkup', 'entered_by')
    readonly_fields = ('created_at',)


@admin.register(BulkImportLog)
class BulkImportLogAdmin(admin.ModelAdmin):
    list_display = (
        'import_type', 'file_name', 'total_records', 'success_count',
        'failed_count', 'status_badge', 'imported_by', 'created_at',
    )
    list_filter = ('import_type', 'status', 'created_at')
    search_fields = ('file_name', 'summary')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'import_type', 'file_name', 'total_records', 'success_count',
        'failed_count', 'status', 'error_report', 'summary',
        'imported_by', 'created_at',
    )
    list_select_related = ('imported_by',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#c4a35a',
            'completed': '#4a7c59',
            'failed': '#a65d57',
            'partial': '#8b6914',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.status,
        )
