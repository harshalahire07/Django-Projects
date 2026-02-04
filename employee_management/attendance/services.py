from .models import Attendance
import datetime

def clock_in_employee(employee_id):
    today = datetime.date.today()
    if Attendance.objects.filter(employee_id=employee_id, date=today, check_out__isnull=True).exists():
        raise ValueError("Already checked in")
    
    attendance = Attendance.objects.create(
        employee_id=employee_id,
        status="Present"
    )
    return attendance

def clock_out_employee(employee_id):
    today = datetime.date.today()
    try:
        attendance = Attendance.objects.get(employee_id=employee_id, date=today, check_out__isnull=True)
        
        attendance.check_out = datetime.datetime.now().time()
        attendance.status = "Checked Out"
        attendance.save()
        return attendance
    except Attendance.DoesNotExist:
        raise ValueError("Not checked in today")
