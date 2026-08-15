from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active_badge', 'user_count', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('name',)
    readonly_fields = ('created_at',)

    @admin.display(description='Status', boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#4a7c59;font-weight:600;">● Active</span>')
        return format_html('<span style="color:#a65d57;font-weight:600;">● Inactive</span>')

    @admin.display(description='Users')
    def user_count(self, obj):
        return obj.users.count()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'get_full_name_display', 'email', 'role_badge',
        'mobile', 'is_active_badge', 'last_login',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'gender', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'mobile')
    ordering = ('username',)
    list_per_page = 30
    date_hierarchy = 'date_joined'
    autocomplete_fields = ('role',)
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'mobile', 'gender', 'profile_photo'),
        }),
        ('Role & Status', {
            'fields': ('role', 'is_active_user', 'is_active', 'is_staff', 'is_superuser'),
        }),
        ('Permissions', {
            'classes': ('collapse',),
            'fields': ('groups', 'user_permissions'),
        }),
        ('Important dates', {
            'classes': ('collapse',),
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'email', 'mobile', 'gender'),
        }),
    )

    actions = ['activate_users', 'deactivate_users']

    @admin.display(description='Full name', ordering='first_name')
    def get_full_name_display(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Role')
    def role_badge(self, obj):
        if not obj.role:
            return '—'
        colors = {
            'admin': '#5c4033', 'super_admin': '#3d2b1f', 'doctor': '#3d5a40',
            'student': '#4a6fa5', 'staff': '#6b5344', 'hod': '#8b6914',
            'staff_family': '#a0896e',
        }
        color = colors.get(obj.role.code, '#666')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.role.name,
        )

    @admin.display(description='Active', boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active and obj.is_active_user

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True, is_active_user=True)
        self.message_user(request, f'{updated} user(s) activated.')

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False, is_active_user=False)
        self.message_user(request, f'{updated} user(s) deactivated.')
