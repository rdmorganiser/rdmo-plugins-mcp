# rdmo-plugins-mcp

Sprint-oriented scaffold for a standalone RDMO MCP server. This version is
meant to be added to Chainlit as an MCP server from the chat window, while also
being runnable from `rdmo-app` with a Django management command.

## Layout

```text
rdmo-plugins-mcp/
├── pyproject.toml
└── rdmo_mcp/
    ├── __init__.py
    ├── server.py
    └── mcp/
        ├── __init__.py
        └── rdmo_client.py
```

## What Is Scaffolded

- A real MCP stdio server entrypoint: `rdmo-mcp-server`
- A Django ORM client for three prototype operations
- MCP tools for:
  - `create_project`
  - `add_project_member`
  - `update_answer`

## Install In `rdmo-app`

Install this repo into the same virtual environment as your local `rdmo-app`:

```bash
pip install -e /path/to/rdmo-plugins-mcp
```

Add the plugin to `INSTALLED_APPS` in `rdmo-app/config/settings/local.py`:

```python
INSTALLED_APPS = ["rdmo_mcp", *INSTALLED_APPS]
```

Optional Django settings for local development:

```python
MCP_TRANSPORT = "sse"          # or "streamable-http" / "stdio"
MCP_HOST = "127.0.0.1"
MCP_PORT = 8090
MCP_DEFAULT_USERNAME = "<your-rdmo-username>"
```

## Run Locally

Start your normal local RDMO and chatbot setup from `rdmo-app`:

```bash
python manage.py runserver
python manage.py runchatbot
python manage.py runmcp
```

## Add It To Chainlit

The chatbot Chainlit config must have MCP enabled. In the Chainlit
`.chainlit/config.toml` used by `runchatbot`, set:

```toml
[features.mcp]
enabled = true

[features.mcp.sse]
enabled = true

[features.mcp.stdio]
enabled = true
allowed_executables = ["rdmo-mcp-server"]
```

Then open `http://localhost:8080`, open the MCP Servers UI, and add either:

1. An HTTP/SSE server, pointing to:

```text
http://127.0.0.1:8090/sse
```

or

2. A stdio server with the command:

```bash
rdmo-mcp-server
```

If you use the stdio variant in Chainlit, pass environment variables such as:

```text
DJANGO_SETTINGS_MODULE=config.settings.local
RDMO_MCP_USERNAME=<your-rdmo-username>
```

## Authentication Caveat

This is an external MCP server from Chainlit's perspective. It does not receive
the authenticated browser user from `rdmo-plugins-chatbot` automatically.

For this prototype, the server acts as:

- the username in `RDMO_MCP_USERNAME`, or
- the optional `username` tool argument

If you want per-user auth later, you will need an explicit auth/context handoff
from the chatbot to the MCP server.

## Notes

- This is a scaffold, not a fully wired production server.
- The exact RDMO model APIs and membership role values may need adjustment in
  the target deployment.
- The exact MCP SDK API may need a small version-specific adjustment once the
  dependency is installed in your environment.
