from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    role = models.CharField(max_length=30, blank=True)
    action = models.CharField(max_length=50, db_index=True)
    module = models.CharField(max_length=50, db_index=True)
    record_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default='success')
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['module', 'action']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp} | {self.user} | {self.module}.{self.action}"
