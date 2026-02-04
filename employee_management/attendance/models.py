from django.db import models
from employee.models import Employee

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.TimeField(auto_now_add=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20)


