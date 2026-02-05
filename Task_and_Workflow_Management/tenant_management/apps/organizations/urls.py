from django.urls import path
from .views import CreateOrganizationAPIView, MyOrganizationsAPIView

urlpatterns = [
    path("create/", CreateOrganizationAPIView.as_view()),
    path("mine/", MyOrganizationsAPIView.as_view()),
]