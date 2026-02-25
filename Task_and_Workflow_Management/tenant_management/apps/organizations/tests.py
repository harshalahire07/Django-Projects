from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMember, Team
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.organizations.rbac_service import has_permission, enforce_organization_isolation

class Phase1ValidationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.super_admin = User.objects.create(email="super@test.com", is_super_admin=True)
        self.super_admin.set_password("Test!123")
        self.super_admin.save()
        
        self.user_admin_a = User.objects.create(email="admin_a@test.com")
        self.user_manager_a = User.objects.create(email="manager_a@test.com")
        self.user_pm_a = User.objects.create(email="pm_a@test.com")
        self.user_member_a1 = User.objects.create(email="member_a1@test.com")
        self.user_member_a2 = User.objects.create(email="member_a2@test.com")
        
        self.user_member_b = User.objects.create(email="member_b@test.com")

        for u in [self.user_admin_a, self.user_manager_a, self.user_pm_a, self.user_member_a1, self.user_member_a2, self.user_member_b]:
            u.set_password("Test!123")
            u.save()

        # Orgs
        self.org_a = Organization.objects.create(name="Org A")
        self.org_b = Organization.objects.create(name="Org B")

        # Teams
        self.team_a1 = Team.objects.create(name="Team A1", organization=self.org_a)
        self.team_a2 = Team.objects.create(name="Team A2", organization=self.org_a)
        self.team_b1 = Team.objects.create(name="Team B1", organization=self.org_b)

        # Memberships Org A
        OrganizationMember.objects.create(user=self.user_admin_a, organization=self.org_a, role=OrganizationMember.ADMIN, team=self.team_a1)
        OrganizationMember.objects.create(user=self.user_manager_a, organization=self.org_a, role=OrganizationMember.MANAGER, team=self.team_a1)
        OrganizationMember.objects.create(user=self.user_pm_a, organization=self.org_a, role=OrganizationMember.PROJECT_MANAGER, team=self.team_a1)
        OrganizationMember.objects.create(user=self.user_member_a1, organization=self.org_a, role=OrganizationMember.MEMBER, team=self.team_a1)
        OrganizationMember.objects.create(user=self.user_member_a2, organization=self.org_a, role=OrganizationMember.MEMBER, team=self.team_a2)

        # Memberships Org B
        OrganizationMember.objects.create(user=self.user_member_b, organization=self.org_b, role=OrganizationMember.MEMBER, team=self.team_b1)

        # Projects
        self.proj_a = Project.objects.create(name="Project A", organization=self.org_a)
        self.proj_b = Project.objects.create(name="Project B", organization=self.org_b)

        # Tasks Org A
        self.task_a1 = Task.objects.create(title="Task A1 (M1)", project=self.proj_a, assigned_to=self.user_member_a1)
        self.task_a2 = Task.objects.create(title="Task A2 (M2)", project=self.proj_a, assigned_to=self.user_member_a2)
        self.task_a_unassigned = Task.objects.create(title="Task A Unassigned", project=self.proj_a)

        # Tasks Org B
        self.task_b1 = Task.objects.create(title="Task B1", project=self.proj_b, assigned_to=self.user_member_b)

    def auth(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_permission_engine(self):
        """D. Permission Engine: Check has_permission works correctly."""
        self.assertTrue(has_permission(self.super_admin, self.org_a.id, OrganizationMember.ADMIN))
        self.assertTrue(has_permission(self.user_admin_a, self.org_a.id, OrganizationMember.ADMIN))
        self.assertTrue(has_permission(self.user_manager_a, self.org_a.id, OrganizationMember.MANAGER))
        self.assertFalse(has_permission(self.user_manager_a, self.org_a.id, OrganizationMember.ADMIN))
        
        # Cross org check
        self.assertFalse(has_permission(self.user_admin_a, self.org_b.id, OrganizationMember.MEMBER))

    def test_multi_tenancy_isolation_db(self):
        """A. Multi-Tenancy Isolation: enforce_organization_isolation limits scope."""
        # Admin A in Org A -> Sees all 3 tasks in Org A
        qs = enforce_organization_isolation(Task.objects.all(), self.org_a.id, user=self.user_admin_a)
        self.assertEqual(qs.count(), 3)
        self.assertNotIn(self.task_b1, qs)

        # Admin A in Org B -> Sees none
        qs_b = enforce_organization_isolation(Task.objects.all(), self.org_b.id, user=self.user_admin_a)
        self.assertEqual(qs_b.count(), 0)

    def test_rbac_hierarchy_task_visibility(self):
        """B. RBAC Hierarchy: Different roles see different task subsets."""
        # MEMBER (A1) sees only task_a1
        qs = enforce_organization_isolation(Task.objects.all(), self.org_a.id, user=self.user_member_a1)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), self.task_a1)

        # PROJECT_MANAGER (Team A1) sees A1 and PM tasks (which is A1) - so task_a1
        qs = enforce_organization_isolation(Task.objects.all(), self.org_a.id, user=self.user_pm_a)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), self.task_a1)

        # MANAGER sees all in org A
        qs = enforce_organization_isolation(Task.objects.all(), self.org_a.id, user=self.user_manager_a)
        self.assertEqual(qs.count(), 3)

        # SUPER_ADMIN sees all in org A (super admin gets infinite role, handles like manager+)
        qs = enforce_organization_isolation(Task.objects.all(), self.org_a.id, user=self.super_admin)
        self.assertEqual(qs.count(), 3)

    def test_team_constraints(self):
        """C. Team Constraints: Cross-org assignment and unique constraints."""
        from django.db import IntegrityError
        # Team must be unique per org implicitly in models (unique_together = ("name", "organization"))
        with self.assertRaises(IntegrityError):
            Team.objects.create(name="Team A1", organization=self.org_a)
        
    def test_api_security_cross_tenant_access(self):
        """E. API Security: Cross-tenant object access blocked."""
        self.auth(self.user_member_b)
        # Attempt to access Org A's tasks API
        url = f"/api/tasks/{self.org_a.id}/{self.proj_a.id}/list/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to update a task from Org A as Org B member
        url2 = f"/api/tasks/{self.task_a1.id}/update-status/"
        res2 = self.client.patch(url2, {"status": "IN_PROGRESS"}, format='json')
        # Isolation catches it at .get() and raises 404 to avoid leaking existence
        self.assertEqual(res2.status_code, status.HTTP_404_NOT_FOUND)

    def test_api_roles_enforcement(self):
        """E. API Security: unauthorized assignment via UI paths blocked."""
        self.auth(self.user_manager_a) # Manager cannot assign tasks (requires Admin)
        url = f"/api/tasks/{self.org_a.id}/{self.task_a1.id}/assign/"
        res = self.client.post(url, {"assigned_to": str(self.user_member_a2.id)}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.auth(self.user_admin_a) # Admin CAN assign tasks
        res = self.client.post(url, {"assigned_to": str(self.user_member_a2.id)}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Try assigning to a member NOT in org A
        res = self.client.post(url, {"assigned_to": str(self.user_member_b.id)}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_api(self):
        """E. API Security: Invalid token / no auth."""
        url = f"/api/tasks/{self.org_a.id}/{self.proj_a.id}/list/"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
