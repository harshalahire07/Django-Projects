from django.urls import path
from .views import (
    CreateOrganizationAPIView,
    MyOrganizationsAPIView,
    OrganizationMembersAPIView,
    AddMemberAPIView,
    TeamListCreateAPIView,
    AssignTeamAPIView,
    PermissionRequestListCreateAPIView,
    PermissionRequestApproveAPIView,
    PermissionRequestRejectAPIView,
)

urlpatterns = [
    path("create/", CreateOrganizationAPIView.as_view()),
    path("mine/", MyOrganizationsAPIView.as_view()),
    path("<uuid:org_id>/members/", OrganizationMembersAPIView.as_view()),
    path("<uuid:org_id>/add_member/", AddMemberAPIView.as_view()),
    path("<uuid:org_id>/teams/", TeamListCreateAPIView.as_view()),
    path("<uuid:org_id>/members/<int:member_uuid>/assign_team/", AssignTeamAPIView.as_view()),
    # Permission escalation
    path("<uuid:org_id>/permission-requests/", PermissionRequestListCreateAPIView.as_view()),
    path("<uuid:org_id>/permission-requests/<uuid:request_id>/approve/", PermissionRequestApproveAPIView.as_view()),
    path("<uuid:org_id>/permission-requests/<uuid:request_id>/reject/", PermissionRequestRejectAPIView.as_view()),
]