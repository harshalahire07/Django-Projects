from django.urls import path
from .views import CreateProjectAPIView, OrganizationProjectsAPIView

urlpatterns = [
    path("<uuid:org_id>/create/", CreateProjectAPIView.as_view()),
    path("<uuid:org_id>/list/", OrganizationProjectsAPIView.as_view()),
]