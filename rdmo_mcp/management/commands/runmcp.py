import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the RDMO MCP server."

    def add_arguments(self, parser):
        parser.add_argument(
            "--transport",
            choices=["stdio", "sse", "streamable-http"],
            default=getattr(settings, "MCP_TRANSPORT", "sse"),
        )
        parser.add_argument(
            "--host",
            default=getattr(settings, "MCP_HOST", "127.0.0.1"),
        )
        parser.add_argument(
            "--port",
            default=str(getattr(settings, "MCP_PORT", 8090)),
        )

    def handle(self, *args, **options):
        env = os.environ.copy()
        env.setdefault("PYTHONPATH", str(Path.cwd()))
        env.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.local"))

        default_username = getattr(settings, "MCP_DEFAULT_USERNAME", None)
        if default_username:
            env["RDMO_MCP_USERNAME"] = default_username

        cmd = [
            sys.executable,
            "-m",
            "rdmo_mcp.server",
            f"--transport={options['transport']}",
        ]

        if options["transport"] != "stdio":
            cmd.extend([
                f"--host={options['host']}",
                f"--port={options['port']}",
            ])

        subprocess.check_call(cmd, env=env, cwd=Path.cwd())
