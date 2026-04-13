"""Minimal hook for exposing MCP tools to the chatbot runtime."""


def setup_mcp_in_chainlit():
    """Import tool definitions when the app is loaded.

    This stays intentionally lightweight for the sprint scaffold: the host
    chatbot app remains responsible for enabling MCP in its Chainlit config.
    """

    from .mcp.tools import register_mcp_tools

    return register_mcp_tools()
