from .models import Attendance
import datetime

def get_today_status(employee_id):
    today = datetime.date.today()
    if Attendance.objects.filter(employee_id=employee_id, date=today, check_out__isnull=True).exists():
        return "Present"
    elif Attendance.objects.filter(employee_id=employee_id, date=today).exists():
        return "Checked Out"
    return "Not Checked In"

def list_attendance(employee_id=None):
    if employee_id:
        return Attendance.objects.filter(employee_id=employee_id)
    return Attendance.objects.all()
