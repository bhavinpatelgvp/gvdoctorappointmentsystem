from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only audit trail – no add/change/delete from admin UI."""

    list_display = (
        'timestamp', 'user', 'role', 'module', 'action',
        'status_badge', 'record_id', 'ip_address',
    )
    list_filter = ('module', 'action', 'status', 'role', 'timestamp')
    search_fields = ('description', 'record_id', 'user__username', 'ip_address')
    date_hierarchy = 'timestamp'
    list_select_related = ('user',)
    list_per_page = 50
    ordering = ('-timestamp',)

    readonly_fields = [f.name for f in AuditLog._meta.fields]

    fieldsets = (
        (None, {
            'fields': ('timestamp', 'user', 'role', 'ip_address'),
        }),
        ('Action', {
            'fields': ('module', 'action', 'record_id', 'status', 'description'),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow superuser delete only for retention housekeeping if needed
        return request.user.is_superuser

    @admin.display(description='Status')
    def status_badge(self, obj):
        color = '#4a7c59' if obj.status == 'success' else '#a65d57'
        return format_html(
            '<span style="color:{};font-weight:600;">● {}</span>', color, obj.status
        )
