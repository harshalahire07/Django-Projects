from django.urls import path
from .views import (
    LoginView, RegisterView, DashboardView, ProjectsView, 
    TasksView, OrgMembersView, OrgAuditView
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("organizations/<uuid:org_id>/members/", OrgMembersView.as_view(), name="org_members"),
    path("organizations/<uuid:org_id>/audit/", OrgAuditView.as_view(), name="org_audit"),
    path("organizations/<uuid:org_id>/projects/", ProjectsView.as_view(), name="org_projects"),
    path("organizations/<uuid:org_id>/projects/<uuid:project_id>/tasks/", TasksView.as_view(), name="project_tasks"),
    path("", LoginView.as_view(), name="root"), # Default to login
]
