from ..services.projects import ProjectService
from ..services.values import ValueService


class RDMOClient:
    """Compatibility wrapper around the new domain-oriented services."""

    def __init__(self, user_identifier):
        self.projects = ProjectService(user_identifier)
        self.values = ValueService(user_identifier)

    def create_project(self, name, catalog_slug, description=""):
        return self.projects.create_project(title=name, catalog_key=catalog_slug, description=description)

    def add_project_member(self, project_id, email, role="author"):
        return self.projects.add_member(project_id=project_id, email=email, role=role)

    def update_catalog_answer(self, project_id, question_id, value, **kwargs):
        return self.values.update_answer(project_id=project_id, question_id=question_id, value=value, **kwargs)
