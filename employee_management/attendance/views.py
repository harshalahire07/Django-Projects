from django.shortcuts import render
from . import selectors

def attendance_index(request):
    attendance_logs = selectors.list_attendance()
    return render(request, 'attendance.html', {'attendance_logs': attendance_logs})
