from django.contrib.auth import get_user_model

from .django import setup_django


class UserService:
    def __init__(self):
        setup_django()
        self.user_model = get_user_model()

    def resolve(self, identifier):
        lookup_fields = ("pk", "id", "username", "email")
        for field in lookup_fields:
            try:
                return self.user_model.objects.get(**{field: identifier})
            except (self.user_model.DoesNotExist, ValueError, TypeError):
                continue
        raise self.user_model.DoesNotExist(f"Unable to resolve user {identifier!r}")

    def resolve_by_email(self, email):
        return self.user_model.objects.get(email=email)
