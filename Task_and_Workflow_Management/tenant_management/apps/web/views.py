from django.views.generic import TemplateView

class LoginView(TemplateView):
    template_name = "web/login.html"

class RegisterView(TemplateView):
    template_name = "web/register.html"

class DashboardView(TemplateView):
    template_name = "web/dashboard.html"

class ProjectsView(TemplateView):
    template_name = "web/projects.html"

class OrgMembersView(TemplateView):
    template_name = "web/org_members.html"

class OrgAuditView(TemplateView):
    template_name = "web/org_audit.html"

class TasksView(TemplateView):
    template_name = "web/tasks.html"
