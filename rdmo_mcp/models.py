from django.db import models


class McpCallLog(models.Model):
    """Optional log model for inspecting prototype tool calls."""

    created = models.DateTimeField(auto_now_add=True)
    tool_name = models.CharField(max_length=128)
    status = models.CharField(max_length=32, default="pending")
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.tool_name} ({self.status})"
