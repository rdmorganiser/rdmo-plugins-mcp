# rdmo-plugins-mcp

Sprint-oriented scaffold for a standalone RDMO MCP plugin. The structure follows
the final standalone-plugin layout from the planning conversation: keep MCP code
separate from `rdmo-plugins-chatbot`, but depend on the chatbot for the actual
Chainlit host runtime.

## Layout

```text
rdmo-plugins-mcp/
├── pyproject.toml
└── rdmo_mcp/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── chainlit_integration.py
    ├── models.py
    └── mcp/
        ├── __init__.py
        ├── rdmo_client.py
        └── tools.py
```

## What Is Scaffolded

- Minimal Django app config: `rdmo_mcp.apps.RdmoMcpConfig`
- Thin ORM wrapper for three prototype operations
- Chainlit-compatible tool functions for:
  - `create_project`
  - `add_project_member`
  - `update_answer`
- Optional `McpCallLog` model for basic prototype logging
- Packaging metadata for installing the plugin as its own repo

## Intended Sprint Integration

Add `rdmo_mcp` to `INSTALLED_APPS` in the host RDMO deployment and keep MCP
enabled in the chatbot's Chainlit config. The chatbot remains the UI/runtime;
this package provides the tool layer.

```python
INSTALLED_APPS = [
    "rdmo_mcp",
    "rdmo_chatbot.plugin",
]
```

The authentication model is the same as in `rdmo-plugins-chatbot`:

- Django sets the signed `chatbot_token` cookie via the chatbot middleware.
- Chainlit authenticates that cookie and stores a `cl.User` in `cl.user_session`.
- The MCP tools read `cl.user_session["user"]` and resolve the RDMO user from
  the same `identifier` value used by the chatbot.

## Local Development

This plugin is not started from this repository directly. It is loaded into your
local `rdmo-app`, just like `rdmo-plugins-chatbot`.

Install both plugins into the same virtual environment used by `rdmo-app`:

```bash
pip install -e /path/to/rdmo-plugins-chatbot[ollama]
pip install -e /path/to/rdmo-plugins-mcp
```

Add both apps in `rdmo-app/config/settings/local.py` and keep the chatbot
middleware and settings:

```python
INSTALLED_APPS = ["rdmo_mcp", "rdmo_chatbot.plugin", *INSTALLED_APPS]
SETTINGS_EXPORT += ["CHATBOT_URL"]

MIDDLEWARE.append("rdmo_chatbot.plugin.middleware.ChatbotMiddleware")

CHATBOT_URL = "http://localhost:8080"
CHATBOT_AUTH_SECRET = "<long-random-secret>"
CHATBOT_ADAPTER = "rdmo_chatbot.chatbot.adapter.OllamaLangChainAdapter"
CHATBOT_LLM_ARGS = {
    "model": "mistral:7b",
}
CHATBOT_STORE = "rdmo_chatbot.chatbot.stores.locmem.LocMemStore"
```

Add the chatbot URLs in `rdmo-app/config/urls.py`:

```python
urlpatterns += [path("api/v1/chatbot/", include("rdmo_chatbot.plugin.urls"))]
```

If you use a custom Chainlit workdir via `CHATBOT_PATH`, enable MCP in that
workdir's `.chainlit/config.toml`:

```toml
[features.mcp]
enabled = true

[features.mcp.sse]
enabled = true

[features.mcp.streamable-http]
enabled = true

[features.mcp.stdio]
enabled = false
```

If you do not use a custom `CHATBOT_PATH`, the default chatbot package config is
used. In that case, you currently need to provide a Chainlit config with MCP
enabled, because the chatbot's default config ships with `features.mcp.enabled =
false`.

Run your local setup from the `rdmo-app` checkout in two terminals:

```bash
python manage.py runserver
```

```bash
python manage.py runchatbot
```

If you use Ollama locally, start that separately as well:

```bash
ollama serve
```

The chatbot UI is then available at `http://localhost:8080`, and the MCP tools
from this plugin are loaded through the same authenticated Chainlit session as
the chatbot itself.

## Notes

- This is a scaffold, not a fully wired production plugin.
- The exact RDMO model APIs and membership role values may need adjustment in
  the target deployment.
- The host chatbot still needs MCP enabled in its `.chainlit/config.toml`.
