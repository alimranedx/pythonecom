from django.db import models
from django.contrib.auth.models import User


class AdminActivityLog(models.Model):
    """Audit trail capturing key back-office staff mutations."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_activity_logs')
    username_snapshot = models.CharField(max_length=150, blank=True, default='')
    action = models.CharField(max_length=100)
    target_model = models.CharField(max_length=80, blank=True, default='')
    target_repr = models.CharField(max_length=255, blank=True, default='')
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.username_snapshot} - {self.action}"
