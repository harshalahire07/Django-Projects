from .models import Employee

def get_employees():
    return Employee.objects.all()

def get_employee(id):
    return Employee.objects.get(id=id)
