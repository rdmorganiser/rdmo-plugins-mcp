from .django import setup_django
from .users import UserService


class ProjectService:
    def __init__(self, user_identifier):
        setup_django()
        self.user_service = UserService()
        self.user = self.user_service.resolve(user_identifier)

    def create_project(self, title, catalog_key, description=""):
        from rdmo.projects.models import Membership, Project
        from rdmo.questions.models import Catalog

        if not self.user.has_perm("projects.add_project"):
            raise PermissionError("You do not have permission to create projects.")

        catalog = self._resolve_catalog(catalog_key)
        project = Project.objects.create(
            title=title,
            description=description,
            catalog=catalog,
            site=getattr(catalog.sites.first(), "pk", None) and catalog.sites.first(),
        )
        Membership.objects.get_or_create(
            project=project,
            user=self.user,
            defaults={"role": "owner"},
        )
        return project

    def add_member(self, project_id, email, role="author"):
        from rdmo.projects.models import Membership, Project

        project = Project.objects.get(pk=project_id)
        member = self.user_service.resolve_by_email(email)

        if role not in {"owner", "manager", "author", "guest"}:
            raise ValueError(f"Unsupported membership role {role!r}.")
        if not self.user.has_perm("projects.add_membership_object", project):
            raise PermissionError("You do not have permission to add project members.")

        membership, created = Membership.objects.get_or_create(
            project=project,
            user=member,
            defaults={"role": role},
        )
        if not created and membership.role != role:
            membership.role = role
            membership.save(update_fields=["role"])

        return {
            "status": "success",
            "membership_id": membership.id,
            "project_id": project.id,
            "email": member.email,
            "role": membership.role,
        }

    def _resolve_catalog(self, catalog_key):
        from rdmo.questions.models import Catalog

        querysets = [
            Catalog.objects.filter(uri_path=catalog_key),
            Catalog.objects.filter(uri=catalog_key),
        ]
        try:
            querysets.append(Catalog.objects.filter(pk=int(catalog_key)))
        except (TypeError, ValueError):
            pass

        for queryset in querysets:
            catalog = queryset.first()
            if catalog is not None:
                return catalog

        raise Catalog.DoesNotExist(f"Unable to resolve catalog {catalog_key!r}")
