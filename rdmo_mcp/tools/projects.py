from asgiref.sync import sync_to_async

from ..services.projects import ProjectService


def _create_project_sync(username, name, catalog_slug, description):
    service = ProjectService(username)
    return service.create_project(title=name, catalog_key=catalog_slug, description=description)


def _add_project_member_sync(username, project_id, email, role):
    service = ProjectService(username)
    return service.add_member(project_id=project_id, email=email, role=role)


def register_project_tools(server):
    @server.tool()
    async def create_project(
        name: str,
        catalog_slug: str,
        description: str = "",
        username: str | None = None,
    ):
        """Create an RDMO project for a catalog identified by uri_path, uri, or id."""

        from ..server import resolve_username

        project = await sync_to_async(_create_project_sync)(
            username=resolve_username(username),
            name=name,
            catalog_slug=catalog_slug,
            description=description,
        )
        return {
            "status": "success",
            "project_id": project.id,
            "title": project.title,
            "catalog_id": project.catalog_id,
        }

    @server.tool()
    async def add_project_member(
        project_id: int,
        email: str,
        role: str = "author",
        username: str | None = None,
    ):
        """Add or update a project member with one of: owner, manager, author, guest."""

        from ..server import resolve_username

        return await sync_to_async(_add_project_member_sync)(
            username=resolve_username(username),
            project_id=project_id,
            email=email,
            role=role,
        )
