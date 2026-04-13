from asgiref.sync import sync_to_async

from ..services.values import ValueService


def _update_answer_sync(username, project_id, question_id, value, collection_index, set_prefix, set_index):
    service = ValueService(username)
    return service.update_answer(
        project_id=project_id,
        question_id=question_id,
        value=value,
        collection_index=collection_index,
        set_prefix=set_prefix,
        set_index=set_index,
    )


def register_value_tools(server):
    @server.tool()
    async def update_answer(
        project_id: int,
        question_id: int,
        value: str,
        username: str | None = None,
        collection_index: int = 0,
        set_prefix: str = "",
        set_index: int = 0,
    ):
        """Update a text answer for a project question."""

        from ..server import resolve_username

        answer = await sync_to_async(_update_answer_sync)(
            username=resolve_username(username),
            project_id=project_id,
            question_id=question_id,
            value=value,
            collection_index=collection_index,
            set_prefix=set_prefix,
            set_index=set_index,
        )
        return {
            "status": "success",
            "answer_id": answer.id,
            "project_id": answer.project_id,
            "attribute_id": answer.attribute_id,
        }
