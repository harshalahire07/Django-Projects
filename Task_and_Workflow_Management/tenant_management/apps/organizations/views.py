from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Organization, OrganizationMember
from .serializers import OrganizationSerializer
# Create your views here.
class CreateOrganizationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = serializer.save()

        OrganizationMember.objects.create(
            user=request.user,
            organization=organization,
            role="ADMIN"
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MyOrganizationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        memberships = OrganizationMember.objects.filter(user=request.user)
        organizations = [m.organization for m in memberships]
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data)