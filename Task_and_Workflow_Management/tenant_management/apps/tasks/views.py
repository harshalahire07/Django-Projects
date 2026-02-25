from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.organizations.models import OrganizationMember
from .serializers import (TaskAssignSerializer,TaskActivitySerializer)
from .models import Task ,TaskActivity
from .serializers import TaskSerializer
from apps.projects.models import Project
from apps.organizations.permissions import IsOrganizationAdmin
from apps.organizations.rbac_service import (
    has_permission, 
    enforce_organization_isolation,
)
from apps.audit.models import AuditLog
from .serializers import TaskStatusUpdateSerializer
ALLOWED_STATUS_TRANSITIONS = {
    "TODO": ["IN_PROGRESS"],
    "IN_PROGRESS": ["DONE"],
    "DONE": [],
}
# Create your views here.
class CreateTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationAdmin]

    def post(self, request, org_id, project_id):
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not Project.objects.filter(id=project_id, organization_id=org_id).exists():
            return Response(
                {"detail": "Project does not belong to this organization"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = serializer.save(project_id=project_id)

        AuditLog.objects.create(
            actor=request.user,
            action="TASK_CREATED",
            description=f"Task '{task.title}' created in project.",
            organization_id=org_id,
        )

        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_201_CREATED
        )

class ProjectTasksAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_id, project_id):
        if not has_permission(request.user, org_id, OrganizationMember.MEMBER):
            return Response(
                {"detail": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate project belongs to organization
        if not Project.objects.filter(id=project_id, organization_id=org_id).exists():
            return Response(
                {"detail": "Project does not belong to this organization"},
                status=status.HTTP_404_NOT_FOUND
            )

        tasks = enforce_organization_isolation(Task.objects.all(), org_id, user=request.user).filter(project_id=project_id)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class AssignTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, org_id, task_id):
        try:
            # 1) Verify ADMIN (or above) of the organization
            if not has_permission(request.user, org_id, OrganizationMember.ADMIN):
                return Response(
                    {"detail": "Only organization admins can assign tasks"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # 2) Load task and ensure it belongs to the org via project
            try:
                task = enforce_organization_isolation(Task.objects.select_related("project"), org_id, user=request.user).get(id=task_id)
            except Task.DoesNotExist:
                return Response({"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

            # 3) Validate assignee
            serializer = TaskAssignSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            assignee = serializer.validated_data["assigned_to"]

            # 4) Ensure assignee is a member of the same organization
            if not has_permission(assignee, org_id, OrganizationMember.MEMBER):
                return Response(
                    {"detail": "Assignee is not a member of this organization"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5) Assign (or reassign) + auto-set status to IN_PROGRESS
            previous_assignee = task.assigned_to
            task.assigned_to = assignee
            if task.status == Task.STATUS_TODO:
                task.status = Task.STATUS_IN_PROGRESS
            task.save(update_fields=["assigned_to", "status", "assigned_at"])
            
            try:
                TaskActivity.objects.create(
                    task=task,
                    actor=request.user,
                    activity_type="ASSIGNED" if previous_assignee is None else "REASSIGNED",
                    message=(
                        f"Task assigned to {assignee.email}"
                        if previous_assignee is None
                        else f"Task reassigned to {assignee.email}"
                    ),
                )

                AuditLog.objects.create(
                    actor=request.user,
                    action="TASK_ASSIGNED" if previous_assignee is None else "TASK_REASSIGNED",
                    description=(
                        f"Task '{task.title}' assigned to {assignee.email}"
                        if previous_assignee is None
                        else f"Task '{task.title}' reassigned to {assignee.email}"
                    ),
                    organization_id=org_id,
                )
            except Exception as e:
                # Log but don't fail the assignment if logging fails
                print(f"Error creating logs: {e}")

            return Response(
                TaskSerializer(task).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"detail": str(e)}, status=500)

class UpdateTaskStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, task_id):
        #  Load task
        try:
            # Secure fetch: only find tasks belonging to organizations where the user has membership
            # or globally if they are super admin.
            is_super_admin = getattr(request.user, 'is_super_admin', False)
            if is_super_admin:
                task_probe = Task.objects.select_related("project").get(id=task_id)
            else:
                user_orgs = OrganizationMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
                task_probe = Task.objects.select_related("project").filter(project__organization_id__in=user_orgs).get(id=task_id)
                
            org_id = task_probe.project.organization_id
            
            # Now enforce specific role constraints (e.g. MEMBER only sees assigned to self)
            task = enforce_organization_isolation(Task.objects.all(), org_id, user=request.user).get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or access denied"}, status=404)

        #  Validate request payload
        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        current_status = task.status
        allowed_next = ALLOWED_STATUS_TRANSITIONS[current_status]

        # Workflow rules enforcement
        if new_status not in allowed_next:
            return Response(
                {"detail": f"Invalid transition from {current_status} to {new_status}"},
                status=400
            )

        # Update status
        task.status = new_status
        task.save(update_fields=["status", "completed_at"])
        TaskActivity.objects.create(
            task=task,
            actor=request.user,
            activity_type="STATUS_CHANGED",
            message=f"Status changed from {current_status} to {new_status}",
        )

        # 7️ Audit log
        AuditLog.objects.create(
            actor=request.user,
            action="STATUS_CHANGED",
            description=f"Task '{task.title}' status changed from {current_status} to {new_status}",
            organization_id=org_id,
        )

        return Response(TaskSerializer(task).data, status=200)

class TaskActivityListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        try:
            is_super_admin = getattr(request.user, 'is_super_admin', False)
            if is_super_admin:
                task_probe = Task.objects.select_related("project").get(id=task_id)
            else:
                user_orgs = OrganizationMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
                task_probe = Task.objects.select_related("project").filter(project__organization_id__in=user_orgs).get(id=task_id)
                
            org_id = task_probe.project.organization_id

            task = enforce_organization_isolation(Task.objects.all(), org_id, user=request.user).get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or access denied"}, status=404)

        activities = task.activities.order_by("-created_at")
        serializer = TaskActivitySerializer(activities, many=True)

        return Response(serializer.data, status=200)
