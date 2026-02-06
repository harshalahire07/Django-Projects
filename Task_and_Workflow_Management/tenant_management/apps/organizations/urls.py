from django.urls import path
from .views import (
    CreateOrganizationAPIView,
    MyOrganizationsAPIView,
    OrganizationMembersAPIView,
)

urlpatterns = [
    path("create/", CreateOrganizationAPIView.as_view()),
    path("mine/", MyOrganizationsAPIView.as_view()),
    path("<uuid:org_id>/members/", OrganizationMembersAPIView.as_view()),
]