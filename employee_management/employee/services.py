from .forms import EmployeeForm

def create_employee(data):
    form = EmployeeForm(data)
    if form.is_valid():
        return form.save()
    raise ValueError(form.errors)

def update_employee(employee, data):
    form = EmployeeForm(data, instance=employee)
    if form.is_valid():
        return form.save()
    raise ValueError(form.errors)

def delete_employee(employee):
    employee.delete()
