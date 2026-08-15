from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'Accounts & Authentication'

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = 'Gujarat Vidyapith Health Administration'
        admin.site.site_title = 'GV Health Admin'
        admin.site.index_title = 'System Control Panel'
        # Optional: custom admin templates path already via TEMPLATES DIRS
