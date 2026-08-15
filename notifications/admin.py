from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'recipient', 'type_badge', 'is_read_flag',
        'email_sent_flag', 'created_at',
    )
    list_filter = ('notification_type', 'is_read', 'email_sent', 'created_at')
    search_fields = ('title', 'message', 'recipient__username', 'recipient__email')
    date_hierarchy = 'created_at'
    list_select_related = ('recipient',)
    autocomplete_fields = ('recipient',)
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    list_per_page = 40

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'appointment': '#4a6fa5',
            'certificate': '#3d5a40',
            'health_report': '#8b6914',
            'reminder': '#c4a35a',
            'system': '#666',
        }
        color = colors.get(obj.notification_type, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_notification_type_display(),
        )

    @admin.display(description='Read', boolean=True)
    def is_read_flag(self, obj):
        return obj.is_read

    @admin.display(description='Email', boolean=True)
    def email_sent_flag(self, obj):
        return obj.email_sent

    @admin.action(description='Mark as read')
    def mark_as_read(self, request, queryset):
        n = queryset.update(is_read=True)
        self.message_user(request, f'{n} notification(s) marked read.')

    @admin.action(description='Mark as unread')
    def mark_as_unread(self, request, queryset):
        n = queryset.update(is_read=False)
        self.message_user(request, f'{n} notification(s) marked unread.')
