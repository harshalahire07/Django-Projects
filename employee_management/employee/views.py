from django.shortcuts import render
from .models import Employee, Department, Role

def employee_list(request):
    departments = Department.objects.all()
    roles = Role.objects.all()
    return render(request, 'index.html', {
        'departments': departments,
        'roles': roles
    })