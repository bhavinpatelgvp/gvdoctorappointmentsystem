from django.contrib import admin
from django.utils.html import format_html
from .models import Patient, StudentProfile, StaffProfile, StaffFamilyProfile


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    extra = 0
    autocomplete_fields = ('programme', 'department')
    classes = ('collapse',)


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    extra = 0
    autocomplete_fields = ('department',)
    classes = ('collapse',)


class StaffFamilyProfileInline(admin.StackedInline):
    model = StaffFamilyProfile
    can_delete = False
    extra = 0
    autocomplete_fields = ('related_staff',)
    classes = ('collapse',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'patient_id', 'name', 'category_badge', 'gender', 'age_display',
        'blood_group', 'mobile', 'status_badge',
    )
    list_filter = ('category', 'status', 'gender', 'blood_group')
    search_fields = (
        'patient_id', 'name', 'mobile', 'email',
        'student_profile__enrollment_number',
        'staff_profile__employee_id',
    )
    list_per_page = 30
    date_hierarchy = 'created_at'
    autocomplete_fields = ('user', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'age_display')
    actions = ['activate_patients', 'deactivate_patients']

    fieldsets = (
        ('Identity', {
            'fields': ('patient_id', 'user', 'category', 'name', 'gender', 'date_of_birth', 'age_display'),
        }),
        ('Contact', {
            'fields': ('email', 'mobile', 'address', 'emergency_contact'),
        }),
        ('Clinical basics', {
            'fields': ('blood_group', 'status'),
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.category == Patient.CATEGORY_STUDENT:
            return [StudentProfileInline]
        if obj.category == Patient.CATEGORY_STAFF:
            return [StaffProfileInline]
        if obj.category == Patient.CATEGORY_STAFF_FAMILY:
            return [StaffFamilyProfileInline]
        return []

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_profile', 'staff_profile', 'family_profile', 'user',
        )

    @admin.display(description='Category')
    def category_badge(self, obj):
        colors = {
            'student': '#4a6fa5',
            'staff': '#6b5344',
            'staff_family': '#8b6914',
        }
        color = colors.get(obj.category, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_category_display(),
        )

    @admin.display(description='Age')
    def age_display(self, obj):
        age = obj.age
        return f'{age} yrs' if age is not None else '—'

    @admin.display(description='Status')
    def status_badge(self, obj):
        color = '#4a7c59' if obj.status == 'Active' else '#a65d57'
        return format_html('<span style="color:{};font-weight:600;">● {}</span>', color, obj.status)

    @admin.action(description='Activate selected patients')
    def activate_patients(self, request, queryset):
        n = queryset.update(status='Active')
        self.message_user(request, f'{n} patient(s) activated.')

    @admin.action(description='Deactivate selected patients')
    def deactivate_patients(self, request, queryset):
        n = queryset.update(status='Inactive')
        self.message_user(request, f'{n} patient(s) deactivated.')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('enrollment_number', 'patient', 'programme', 'department', 'semester')
    list_filter = ('department', 'programme', 'semester')
    search_fields = ('enrollment_number', 'patient__name', 'patient__patient_id')
    autocomplete_fields = ('patient', 'programme', 'department')
    list_select_related = ('patient', 'programme', 'department')


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'patient', 'department', 'designation')
    list_filter = ('department', 'designation')
    search_fields = ('employee_id', 'patient__name', 'designation')
    autocomplete_fields = ('patient', 'department')
    list_select_related = ('patient', 'department')


@admin.register(StaffFamilyProfile)
class StaffFamilyProfileAdmin(admin.ModelAdmin):
    list_display = ('patient', 'relationship', 'related_staff')
    list_filter = ('relationship',)
    search_fields = ('patient__name', 'related_staff__employee_id', 'related_staff__patient__name')
    autocomplete_fields = ('patient', 'related_staff')
    list_select_related = ('patient', 'related_staff', 'related_staff__patient')
