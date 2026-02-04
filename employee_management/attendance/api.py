import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from . import services, selectors
from employee.api import jwt_required

@require_http_methods(["POST"])
@jwt_required
def clock_in(request):
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        services.clock_in_employee(employee_id)
        return JsonResponse({'message': 'Checked in successfully'})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["POST"])
@jwt_required
def clock_out(request):
    try:
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        services.clock_out_employee(employee_id)
        return JsonResponse({'message': 'Checked out successfully'})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
@jwt_required
def get_attendance(request, employee_id):
    logs = selectors.list_attendance(employee_id)
    data = [{
        'date': log.date,
        'check_in': log.check_in,
        'check_out': log.check_out,
        'status': log.status
    } for log in logs]
    return JsonResponse(data, safe=False)
