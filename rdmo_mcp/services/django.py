import os

import django
from django.apps import apps


def setup_django():
    if apps.ready:
        return
    if not os.getenv("DJANGO_SETTINGS_MODULE"):
        raise RuntimeError("DJANGO_SETTINGS_MODULE is not set.")
    django.setup()
