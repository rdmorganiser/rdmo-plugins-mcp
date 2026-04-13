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
    ├── adapter.py
    ├── apps.py
    ├── server.py
    ├── services/
    │   ├── django.py
    │   ├── projects.py
    │   ├── users.py
    │   └── values.py
    └── tools/
        ├── projects.py
        └── values.py
```

## What Is Scaffolded

- A real MCP stdio server entrypoint: `rdmo-mcp-server`
- Domain-oriented services aligned with RDMO apps (`projects`, `questions`/values, users)
- MCP tools for:
  - `create_project`
  - `add_project_member`
  - `update_answer`
- Reusable chatbot adapters in `rdmo_mcp.adapter` that connect an LLM to the
  MCP server

## Install In `rdmo-app`

Install this repo into the same virtual environment as your local `rdmo-app`:

```bash
pip install -e /path/to/rdmo-plugins-mcp
```

Add the plugin to `INSTALLED_APPS` in `rdmo-app/config/settings/local.py`:

```python
INSTALLED_APPS = ["rdmo_mcp", *INSTALLED_APPS]
```

If you also use `rdmo-plugins-chatbot`, the MCP plugin is intended to run
alongside a chatbot Chainlit workdir:

```python
INSTALLED_APPS = ["rdmo_mcp", "rdmo_chatbot.plugin", *INSTALLED_APPS]
```

Optional Django settings for local development:

```python
MCP_TRANSPORT = "sse"          # or "streamable-http" / "stdio"
MCP_HOST = "127.0.0.1"
MCP_PORT = 8090
MCP_DEFAULT_USERNAME = "<your-rdmo-username>"

CHATBOT_MCP_SERVER_TRANSPORT = "sse"
CHATBOT_MCP_SERVER_URL = "http://127.0.0.1:8090/sse"
CHATBOT_MCP_MAX_STEPS = 8
```

To let the chatbot LLM actually call the MCP tools, point `CHATBOT_ADAPTER` to
one of the MCP-aware adapters from this plugin:

```python
CHATBOT_ADAPTER = "rdmo_mcp.adapter.OpenAIMCPLangChainAdapter"
```

or

```python
CHATBOT_ADAPTER = "rdmo_mcp.adapter.OllamaMCPLangChainAdapter"
```

## Create A Chainlit Workdir In A New `rdmo-app`

If your `rdmo-app` does not yet have a chatbot Chainlit workdir, create one
from the chatbot plugin defaults. Run this from the `rdmo-app` checkout and the
same virtual environment:

```bash
python manage.py make_chatbot_theme --path /absolute/path/to/rdmo-app/chatbot_chainlit
```

This copies the files expected by `rdmo-plugins-chatbot`:

- `.chainlit/config.toml`
- `.chainlit/translations/`
- `chainlit.md`
- `chainlit_en-US.md`
- `chainlit_de-DE.md`
- `public/`

Then point the chatbot settings to that workdir:

```python
CHATBOT_PATH = "chatbot_chainlit"
```

If you already have a custom `CHATBOT_PATH`, you can run the same command with
that target path. It will skip files that already exist and copy any missing
defaults, which is useful if your workdir is missing `.chainlit/config.toml` or
`public/`.

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

If you created the workdir with `make_chatbot_theme`, edit the copied
`chatbot_chainlit/.chainlit/config.toml` and add the MCP settings there.

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
