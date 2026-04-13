from django.apps import AppConfig


class RdmoMcpConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rdmo_mcp"
    verbose_name = "RDMO MCP Tools"

    def ready(self):
        from .chainlit_integration import setup_mcp_in_chainlit

        setup_mcp_in_chainlit()
