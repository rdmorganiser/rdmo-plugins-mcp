from .projects import register_project_tools
from .values import register_value_tools


def register_tools(server):
    register_project_tools(server)
    register_value_tools(server)
