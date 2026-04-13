import argparse
import os

from mcp.server.fastmcp import FastMCP

from .mcp.rdmo_client import RDMOClient


def _resolve_username(username: str | None) -> str:
    resolved = username or os.getenv("RDMO_MCP_USERNAME")
    if not resolved:
        raise ValueError(
            "A username is required. Pass it to the tool or set RDMO_MCP_USERNAME."
        )
    return resolved


def create_server(host: str, port: int) -> FastMCP:
    server = FastMCP("RDMO MCP", host=host, port=port)

    @server.tool()
    def create_project(
        name: str,
        catalog_slug: str,
        description: str = "",
        username: str | None = None,
    ):
        """Create an RDMO project for a given catalog slug."""

        client = RDMOClient(_resolve_username(username))
        project = client.create_project(name=name, catalog_slug=catalog_slug, description=description)
        return {
            "status": "success",
            "project_id": project.id,
            "title": project.title,
        }

    @server.tool()
    def add_project_member(project_id: int, email: str, username: str | None = None):
        """Add a member to an RDMO project."""

        client = RDMOClient(_resolve_username(username))
        return client.add_project_member(project_id=project_id, email=email)

    @server.tool()
    def update_answer(
        project_id: int,
        question_id: int,
        value: str,
        username: str | None = None,
    ):
        """Update an RDMO answer value by project and question id."""

        client = RDMOClient(_resolve_username(username))
        answer = client.update_catalog_answer(
            project_id=project_id,
            question_id=question_id,
            value=value,
        )
        return {
            "status": "success",
            "answer_id": answer.id,
        }

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
