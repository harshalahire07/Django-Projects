import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Employee
from . import services, selectors
from attendance import selectors as attendance_selectors
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
        'current_status': attendance_selectors.get_today_status(employee.id),
    }

SECRET_KEY = settings.SECRET_KEY  
@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        print(f"Login Attempt: Username={username}")
        
        user = authenticate(request, username=username, password=password)
        if user is None:
             # Fallback for older Django versions or backends not using request
             user = authenticate(username=username, password=password)
             
        print(f"Authentication Result: {user}")
        
        if user is not None:
            payload = {
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                'iat': datetime.datetime.utcnow()
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return JsonResponse({'token': token, 'username': user.username})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except json.JSONDecodeError:
        print("Login Error: Invalid JSON body")
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        print(f"Login Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
            
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
            
        return f(request, *args, **kwargs)
    return decorator

@csrf_exempt
@require_http_methods(["GET", "POST"])
def EmployeeListApi(request):
    if request.method == 'GET':
        employees = selectors.get_employees()
        data = [serialize_employee(emp) for emp in employees]
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        @jwt_required
        def protected_post(req):
            try:
                data = json.loads(req.body)
                employee = services.create_employee(data)
                return JsonResponse(serialize_employee(employee), status=201)
            except ValueError as e:
                return JsonResponse({'errors': e.args[0]}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        return protected_post(request)

@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
@jwt_required
def EmployeeDetailApi(request, id):
    try:
        employee = selectors.get_employee(id)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(serialize_employee(employee))

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            employee = services.update_employee(employee, data)
            return JsonResponse(serialize_employee(employee))
        except ValueError as e:
            return JsonResponse({'errors': e.args[0]}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        services.delete_employee(employee)
        return JsonResponse({}, status=204)
