from functools import wraps

from .rdmo_client import RDMOClient

try:
    import chainlit as cl
except ImportError:  # pragma: no cover - optional during packaging/editing
    cl = None


def _tool_step(name):
    def decorator(func):
        if cl is None:
            return func
        return cl.step(name=name, type="tool")(func)

    return decorator


def _serialise_error(exc):
    return {"status": "error", "error": str(exc)}


def _get_user_identifier():
    if cl is None:
        raise RuntimeError("Chainlit is not installed.")

    user = cl.user_session.get("user")
    if user is None:
        raise PermissionError("User not authenticated.")

    return getattr(user, "identifier", user)


@_tool_step("Create RDMO Project")
async def create_project(name: str, catalog_slug: str, description: str = ""):
    try:
        client = RDMOClient(_get_user_identifier())
        project = client.create_project(name, catalog_slug, description)
        return {
            "status": "success",
            "project_id": project.id,
            "title": project.title,
        }
    except Exception as exc:  # pragma: no cover - sprint scaffold error surface
        return _serialise_error(exc)


@_tool_step("Add Project Member")
async def add_project_member(project_id: int, email: str):
    try:
        client = RDMOClient(_get_user_identifier())
        return client.add_project_member(project_id, email)
    except Exception as exc:  # pragma: no cover - sprint scaffold error surface
        return _serialise_error(exc)


@_tool_step("Update Catalog Answer")
async def update_answer(project_id: int, question_id: int, value: str):
    try:
        client = RDMOClient(_get_user_identifier())
        answer = client.update_catalog_answer(project_id, question_id, value)
        return {
            "status": "success",
            "answer_id": answer.id,
        }
    except Exception as exc:  # pragma: no cover - sprint scaffold error surface
        return _serialise_error(exc)


def register_mcp_tools():
    """Return the tool callables so the host app can introspect or register them."""

    return {
        "create_project": create_project,
        "add_project_member": add_project_member,
        "update_answer": update_answer,
    }
