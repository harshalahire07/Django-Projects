import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_management.settings')
django.setup()

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMember, Team
from apps.projects.models import Project
from apps.tasks.models import Task

def setup_test_data():
    org = Organization.objects.first()
    if not org:
        org = Organization.objects.create(name="QA Org", description="For testing")

    team1, _ = Team.objects.get_or_create(name="Team A", organization=org)
    team2, _ = Team.objects.get_or_create(name="Team B", organization=org)

    proj, _ = Project.objects.get_or_create(name="Test Iso Project", description="Testing task isolation", organization=org)

    def get_or_create_user(email, role, team=None):
        u, _ = User.objects.get_or_create(email=email)
        u.set_password('Test!123')
        u.save()
        OrganizationMember.objects.update_or_create(user=u, organization=org, defaults={"role": role, "team": team})
        return u

    admin = get_or_create_user("qa_admin@test.com", OrganizationMember.ADMIN, team1)
    manager = get_or_create_user("qa_manager@test.com", OrganizationMember.MANAGER, team1)
    pm = get_or_create_user("qa_pm@test.com", OrganizationMember.PROJECT_MANAGER, team1)
    member1 = get_or_create_user("qa_member@test.com", OrganizationMember.MEMBER, team1)
    member2 = get_or_create_user("qa_other@test.com", OrganizationMember.MEMBER, team2)

    # create tasks in the project
    t1, _ = Task.objects.get_or_create(title="Task for Member 1", project=proj, assigned_to=member1)
    t2, _ = Task.objects.get_or_create(title="Task for Other Member", project=proj, assigned_to=member2)
    t3, _ = Task.objects.get_or_create(title="Unassigned Task", project=proj)
    t4, _ = Task.objects.get_or_create(title="Task for PM", project=proj, assigned_to=pm)

    print(f"Data ready. Project: {proj.name}")

if __name__ == '__main__':
    setup_test_data()
