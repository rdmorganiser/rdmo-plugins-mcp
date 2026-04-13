import argparse
import os

from mcp.server.fastmcp import FastMCP

from .tools import register_tools


def resolve_username(username: str | None) -> str:
    resolved = username or os.getenv("RDMO_MCP_USERNAME")
    if not resolved:
        raise ValueError(
            "A username is required. Pass it to the tool or set RDMO_MCP_USERNAME."
        )
    return resolved


def create_server(host: str, port: int) -> FastMCP:
    server = FastMCP("RDMO MCP", host=host, port=port)
    register_tools(server)
    return server


def main():
    parser = argparse.ArgumentParser(description="Run the RDMO MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=os.getenv("RDMO_MCP_TRANSPORT", "stdio"),
    )
    parser.add_argument(
        "--host",
        default=os.getenv("RDMO_MCP_HOST", "127.0.0.1"),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("RDMO_MCP_PORT", "8090")),
    )
    args = parser.parse_args()
    server = create_server(host=args.host, port=args.port)

    if args.transport == "stdio":
        server.run()
        return

    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
