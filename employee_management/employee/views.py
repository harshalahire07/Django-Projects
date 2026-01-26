from django.shortcuts import render , HttpResponse, redirect
from .models import Employee,Role,Department
# Create your views here.

def home(request):
    return render(request, 'index.html')

def add_employee(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        department_name = request.POST.get('department')
        role_name = request.POST.get('role')

        if not all([first_name, last_name, email, phone, address, department_name, role_name]):
             return render(request, 'add_employee.html', {'message': 'Missing fields'})

        try:
            phone = int(phone)
        except ValueError:
            return render(request, 'add_employee.html', {'message': 'Invalid phone number'})

        try:
            department = Department.objects.get(name=department_name)
            role = Role.objects.get(name=role_name)
        except (Department.DoesNotExist, Role.DoesNotExist):
            return render(request, 'add_employee.html', {'message': 'Invalid Department or Role selected'})

        employee = Employee(
            first_name=first_name, 
            last_name=last_name, 
            email=email, 
            phone=phone, 
            address=address, 
            department=department, 
            role=role
        )
        employee.save()
        return render(request, 'add_employee.html', {'message': 'Employee added successfully'})
    elif request.method == 'GET':
        return render(request, 'add_employee.html')
    else:
        return render(request, 'add_employee.html', {'message': 'Invalid request method'})

def remove_employee(request, employee_id=0):
    context = {}
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            employee.delete()
            context['message'] = "Employee removed successfully"
        except Employee.DoesNotExist:
            context['message'] = "Employee not found"

    employees = Employee.objects.all()
    context['employees'] = employees
    
    return render(request, 'remove_employee.html', context)

def update_employee(request, employee_id=0):
    context = {}
    employees = Employee.objects.all()
    context['employees'] = employees

    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            context['employee'] = employee
        except Employee.DoesNotExist:
             context['message'] = "Employee not found"
             return render(request, 'update_employee.html', context)

        if request.method == 'POST':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            department_name = request.POST.get('department')
            role_name = request.POST.get('role')

            if not all([first_name, last_name, email, phone, address, department_name, role_name]):
                context['message'] = "Missing fields"
                return render(request, 'update_employee.html', context)
            
            try:
                phone = int(phone)
                department = Department.objects.get(name=department_name)
                role = Role.objects.get(name=role_name)
                
                employee.first_name = first_name
                employee.last_name = last_name
                employee.email = email
                employee.phone = phone
                employee.address = address
                employee.department = department
                employee.role = role
                employee.save()
                
                context['message'] = "Employee updated successfully"
               
                context['employee'] = employee
            except ValueError:
                 context['message'] = "Invalid phone number"
            except (Department.DoesNotExist, Role.DoesNotExist):
                 context['message'] = "Invalid Department or Role"

    return render(request, 'update_employee.html', context)

def view_all_employees(request):
    employees = Employee.objects.all()
    context={   
        'employees':employees
    }
    return render(request, 'view_all_employees.html',context)