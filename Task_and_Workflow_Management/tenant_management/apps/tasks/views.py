from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.organizations.models import OrganizationMember
from .serializers import TaskAssignSerializer
from .models import Task
from .serializers import TaskSerializer
from apps.projects.models import Project
from apps.organizations.permissions import IsOrganizationAdmin
# Create your views here.
class CreateTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]

    def post(self, request, org_id, project_id):
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = serializer.save(project_id=project_id)

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED
        )

class ProjectTasksAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id, project_id):
        is_member = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id
        ).exists()

        if not is_member:
            return Response(
                {"detail": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        tasks = Task.objects.filter(project_id=project_id)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

class UpdateTaskStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, task_id):
        task = Task.objects.get(id=task_id)

        if task.assigned_to != request.user:
            return Response(
                {"detail": "Only assigned user can update status"},
                status=status.HTTP_403_FORBIDDEN
            )

        task.status = request.data.get("status", task.status)
        task.save()

        return Response(TaskSerializer(task).data)

class AssignTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, org_id, task_id):
        # 1) Verify ADMIN of the organization
        is_admin = OrganizationMember.objects.filter(
            user=request.user,
            organization_id=org_id,
            role="ADMIN"
        ).exists()

        if not is_admin:
            return Response(
                {"detail": "Only organization admins can assign tasks"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2) Load task and ensure it belongs to the org via project
        try:
            task = Task.objects.select_related("project").get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        if str(task.project.organization_id) != str(org_id):
            return Response(
                {"detail": "Task does not belong to this organization"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3) Validate assignee
        serializer = TaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignee = serializer.validated_data["assigned_to"]

        # 4) Ensure assignee is a member of the same organization
        is_member = OrganizationMember.objects.filter(
            user=assignee,
            organization_id=org_id
        ).exists()

        if not is_member:
            return Response(
                {"detail": "Assignee is not a member of this organization"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5) Assign (or reassign)
        task.assigned_to = assignee
        task.save(update_fields=["assigned_to"])

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )