import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Employee, Department, Role
from .forms import EmployeeForm

def serialize_employee(employee):
    return {
        'id': employee.id,
        'first_name': employee.first_name,
        'last_name': employee.last_name,
        'email': employee.email,
        'phone': employee.phone,
        'address': employee.address,
        'department_id': employee.department.id,
        'department_name': employee.department.name,
        'role_id': employee.role.id,
        'role_name': employee.role.name,
    }

@csrf_exempt
@require_http_methods(["GET", "POST"])
def EmployeeListApi(request):
    if request.method == 'GET':
        employees = Employee.objects.all()
        data = [serialize_employee(emp) for emp in employees]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = EmployeeForm(data)
            if form.is_valid():
                employee = form.save()
                return JsonResponse(serialize_employee(employee), status=201)
            else:
                return JsonResponse({'errors': form.errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def EmployeeDetailApi(request, id):
    try:
        employee = Employee.objects.get(id=id)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_employee(employee))

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            form = EmployeeForm(data, instance=employee)
            if form.is_valid():
                employee = form.save()
                return JsonResponse(serialize_employee(employee))
            else:
                return JsonResponse({'errors': form.errors}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        employee.delete()
        return JsonResponse({}, status=204)
