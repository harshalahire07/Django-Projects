import json
from django.http import JsonResponse

from django.views.decorators.http import require_http_methods
from .models import Employee, Department, Role
from .forms import EmployeeForm
import jwt
import datetime
from django.conf import settings
from django.contrib.auth import authenticate

from functools import wraps

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



SECRET_KEY = settings.SECRET_KEY  

@require_http_methods(["POST"])
def login_api(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Create Token
            payload = {
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24), # Token expires in 24 hours
                'iat': datetime.datetime.utcnow()
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return JsonResponse({'token': token, 'username': user.username})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def jwt_required(f):
    @wraps(f)
    def decorator(request, *args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return JsonResponse({'error': 'Token is missing'}, status=401)
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            # Verify Token
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            # We could attach user to request here if needed: request.jwt_user_id = payload['user_id']
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
            
        return f(request, *args, **kwargs)
    return decorator



@require_http_methods(["GET", "POST"])
def EmployeeListApi(request):
    if request.method == 'GET':
        employees = Employee.objects.all()
        data = [serialize_employee(emp) for emp in employees]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':

        @jwt_required
        def protected_post(req):
            try:
                data = json.loads(req.body)
                form = EmployeeForm(data)
                if form.is_valid():
                    employee = form.save()
                    return JsonResponse(serialize_employee(employee), status=201)
                else:
                    return JsonResponse({'errors': form.errors}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        return protected_post(request)

@require_http_methods(["GET", "PUT", "DELETE"])
@jwt_required
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
