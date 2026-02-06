from django.urls import path
from .views import (
    CreateTaskAPIView,
    ProjectTasksAPIView,
    UpdateTaskStatusAPIView,
    AssignTaskAPIView,
)

urlpatterns = [
    path(
        "<uuid:org_id>/<uuid:project_id>/create/",
        CreateTaskAPIView.as_view()
    ),
    path(
        "<uuid:org_id>/<uuid:project_id>/list/",
        ProjectTasksAPIView.as_view()
    ),
    path(
        "<uuid:task_id>/update-status/",
        UpdateTaskStatusAPIView.as_view()
    ),
    path(
    "<uuid:org_id>/<uuid:task_id>/assign/",
    AssignTaskAPIView.as_view()
    ),
]