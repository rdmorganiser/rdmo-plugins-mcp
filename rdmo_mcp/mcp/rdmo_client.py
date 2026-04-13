import os

import django
from django.apps import apps
from django.contrib.auth import get_user_model


def _setup_django():
    if apps.ready:
        return
    if not os.getenv("DJANGO_SETTINGS_MODULE"):
        raise RuntimeError("DJANGO_SETTINGS_MODULE is not set.")
    django.setup()


class RDMOClient:
    """Thin Django ORM wrapper used by the MCP server."""

    def __init__(self, user_identifier):
        _setup_django()
        self.user_model = get_user_model()
        self.user = self._resolve_user(user_identifier)

    def create_project(self, name, catalog_slug, description=""):
        from rdmo.questions.models.catalog import Catalog
        from rdmo.projects.models import Membership, Project

        catalog = Catalog.objects.get(slug=catalog_slug)
        project = Project.objects.create(
            title=name,
            description=description,
            created_by=self.user,
        )
        project.catalogs.add(catalog)
        Membership.objects.get_or_create(
            project=project,
            user=self.user,
            defaults={"role": "manager"},
        )
        return project

    def add_project_member(self, project_id, email):
        from rdmo.projects.models import Membership, Project
        from django.contrib.auth import get_user_model

        project = Project.objects.get(pk=project_id)
        member = get_user_model().objects.get(email=email)

        if not self._has_permission(project, "manager"):
            raise PermissionError("You do not have permission to add members.")

        Membership.objects.get_or_create(
            project=project,
            user=member,
            defaults={"role": "member"},
        )
        return {"status": "success", "email": email}

    def update_catalog_answer(self, project_id, question_id, value):
        from rdmo.projects.models import Membership, Project, Value
        from rdmo.questions.models import Question

        project = Project.objects.get(pk=project_id)
        question = Question.objects.get(pk=question_id)

        if not self._has_permission(project, "editor"):
            raise PermissionError("You do not have permission to edit this project.")

        answer, _ = Value.objects.get_or_create(project=project, question=question)
        answer.value = value
        answer.save()
        return answer

    def _resolve_user(self, identifier):
        lookup_fields = ("pk", "id", "username", "email")
        for field in lookup_fields:
            try:
                return self.user_model.objects.get(**{field: identifier})
            except (self.user_model.DoesNotExist, ValueError, TypeError):
                continue
        raise self.user_model.DoesNotExist(f"Unable to resolve user {identifier!r}")

    def _has_permission(self, project, minimum_role):
        from rdmo.projects.models import Membership

        membership = Membership.objects.filter(project=project, user=self.user).first()
        if membership is None:
            return False

        roles = ["member", "editor", "manager"]
        return roles.index(membership.role) >= roles.index(minimum_role)
