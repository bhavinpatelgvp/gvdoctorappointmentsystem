from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_APPOINTMENT = 'appointment'
    TYPE_CERTIFICATE = 'certificate'
    TYPE_HEALTH_REPORT = 'health_report'
    TYPE_REMINDER = 'reminder'
    TYPE_SYSTEM = 'system'

    TYPE_CHOICES = [
        (TYPE_APPOINTMENT, 'Appointment'),
        (TYPE_CERTIFICATE, 'Medical Certificate'),
        (TYPE_HEALTH_REPORT, 'Health Report'),
        (TYPE_REMINDER, 'Reminder'),
        (TYPE_SYSTEM, 'System'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.recipient}"
