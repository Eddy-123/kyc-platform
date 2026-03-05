import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=255)
    target_type = models.CharField(max_length=100)
    target_id = models.UUIDField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["created_at"]),
        ]
