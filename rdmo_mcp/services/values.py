from .django import setup_django
from .users import UserService


class ValueService:
    def __init__(self, user_identifier):
        setup_django()
        self.user_service = UserService()
        self.user = self.user_service.resolve(user_identifier)

    def update_answer(
        self,
        project_id,
        question_id,
        value,
        *,
        collection_index=0,
        set_prefix="",
        set_index=0,
    ):
        from rdmo.projects.models import Project, Value
        from rdmo.questions.models import Question

        project = Project.objects.get(pk=project_id)
        question = Question.objects.get(pk=question_id)

        if question.attribute is None:
            raise ValueError("The question has no attribute and cannot be answered via MCP.")
        if not self.user.has_perm("projects.change_value_object", project):
            raise PermissionError("You do not have permission to change project answers.")

        answer, _ = Value.objects.get_or_create(
            project=project,
            snapshot=None,
            attribute=question.attribute,
            set_prefix=set_prefix,
            set_index=set_index,
            collection_index=collection_index,
            defaults={
                "value_type": question.value_type,
                "unit": question.unit,
                "set_collection": question.is_collection,
            },
        )
        answer.text = value
        answer.option = None
        answer.external_id = ""
        answer.value_type = question.value_type
        answer.unit = question.unit
        answer.set_collection = question.is_collection
        answer.save()
        return answer
