from django.urls import path
from .views import AuditLogListAPIView

urlpatterns = [
    path(
        "<uuid:org_id>/logs/",
        AuditLogListAPIView.as_view(),
        name="audit-log-list"
    ),
]
